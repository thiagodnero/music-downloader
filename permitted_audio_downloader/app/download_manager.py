from __future__ import annotations

import tempfile
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from PySide6 import QtCore

from permitted_audio_downloader.app import ffmpeg_service
from permitted_audio_downloader.app.utils import resolve_output_path, sanitize_filename
from permitted_audio_downloader.app.validators import (
    ValidationError,
    get_source_label,
    validate_url,
)
from permitted_audio_downloader.app.ytdlp_service import download_audio


class JobStatus(str, Enum):
    QUEUED = "Na fila"
    RUNNING = "Baixando"
    DONE = "Concluído"
    ERROR = "Falhou"
    CANCELED = "Cancelado"


@dataclass
class DownloadJob:
    id: int
    url: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    title: str | None = None
    output_path: str | None = None
    error_message: str | None = None


class DownloadWorker(QtCore.QObject):
    progress = QtCore.Signal(int, float, str, str)
    status = QtCore.Signal(int, str)
    metadata = QtCore.Signal(int, str, str)
    finished = QtCore.Signal(int, str)
    failed = QtCore.Signal(int, str)
    log = QtCore.Signal(int, str)

    def __init__(self, job: DownloadJob, options: dict):
        super().__init__()
        self.job = job
        self.options = options
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def _check_cancel(self) -> None:
        if self._cancel_requested:
            raise RuntimeError("Download cancelado")

    @QtCore.Slot()
    def run(self) -> None:
        try:
            self.status.emit(self.job.id, JobStatus.RUNNING.value)
            self.log.emit(self.job.id, f"Job {self.job.id} running")
            with tempfile.TemporaryDirectory() as temp_dir:
                def hook(data: dict) -> None:
                    if data.get("status") == "downloading":
                        downloaded = data.get("downloaded_bytes") or 0
                        total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                        percent = (downloaded / total * 100) if total else 0.0
                        speed = data.get("speed")
                        eta = data.get("eta")
                        speed_text = f"{(speed or 0) / 1024:.1f} KiB/s" if speed else "-"
                        eta_text = str(eta) if eta is not None else "-"
                        self.progress.emit(self.job.id, percent, speed_text, eta_text)
                    self._check_cancel()

                info = download_audio(
                    self.job.url,
                    temp_dir,
                    progress_callback=hook,
                    ffmpeg_location=self.options.get("ffmpeg_bin_dir"),
                )
                self._check_cancel()

                title = info.get("title") or "audio"
                uploader = info.get("uploader") or ""
                source = get_source_label(self.job.url)
                self.metadata.emit(self.job.id, title, source)

                filename = title
                if self.options["preserve_name"] and uploader:
                    filename = f"{uploader} - {title}"
                filename = sanitize_filename(filename)
                output_path = resolve_output_path(
                    self.options["output_dir"],
                    filename,
                    self.options["overwrite"],
                )

                requested = info.get("requested_downloads") or []
                filepath = (
                    requested[0].get("filepath") if requested else info.get("filepath")
                ) or info.get("_filename")
                if not filepath:
                    raise RuntimeError("Arquivo de download não localizado")

                ffmpeg_service.convert_to_wav(
                    str(Path(filepath)),
                    str(output_path),
                    self.options["sample_rate"],
                )
                self.progress.emit(self.job.id, 100.0, "-", "0")
                self.finished.emit(self.job.id, str(output_path))
                self.log.emit(self.job.id, f"Job {self.job.id} done")
        except Exception as exc:
            message = "Cancelado" if "cancelado" in str(exc).lower() else str(exc)
            self.failed.emit(self.job.id, message)
            self.log.emit(self.job.id, f"Job {self.job.id} failed: {message}")


class DownloadManager(QtCore.QObject):
    job_added = QtCore.Signal(object)
    job_updated = QtCore.Signal(object)
    log_message = QtCore.Signal(str)
    queue_empty = QtCore.Signal()

    def __init__(self, options: dict):
        super().__init__()
        self.options = options
        self.jobs: list[DownloadJob] = []
        self._queue: deque[DownloadJob] = deque()
        self._current: DownloadJob | None = None
        self._worker_thread: Optional[QtCore.QThread] = None
        self._worker: Optional[DownloadWorker] = None
        self._is_running = False
        self._next_job_id = 1

    def add_job(self, url: str) -> int:
        validate_url(url)
        job = DownloadJob(id=self._next_job_id, url=url)
        self._next_job_id += 1
        self.jobs.append(job)
        self._queue.append(job)
        self.job_added.emit(job)
        self.log_message.emit(f"Job {job.id} queued")
        return job.id

    def start(self) -> None:
        if self._is_running:
            return
        self.start_next()

    @QtCore.Slot()
    def start_next(self) -> None:
        if self._is_running:
            return
        next_job = self._pop_next_queued()
        if not next_job:
            self.log_message.emit("Queue empty, idle")
            self.queue_empty.emit()
            return

        self._current = next_job
        self._is_running = True
        next_job.status = JobStatus.RUNNING
        self.job_updated.emit(next_job)
        self.log_message.emit(f"Starting next job {next_job.id}")

        self._worker_thread = QtCore.QThread(self)
        self._worker = DownloadWorker(next_job, self.options)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.status.connect(self._on_worker_status)
        self._worker.metadata.connect(self._on_worker_metadata)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.log.connect(self._on_worker_log)

        self._worker_thread.start()

    def _pop_next_queued(self) -> DownloadJob | None:
        while self._queue:
            job = self._queue.popleft()
            if job.status == JobStatus.QUEUED:
                return job
        return None

    def cancel(self, job_id: int) -> None:
        queued_job = self._find_job(job_id)
        if not queued_job:
            return
        if self._current and self._current.id == job_id and self._worker:
            self._worker.request_cancel()
            self.log_message.emit(f"Job {job_id} cancel requested")
            return
        if queued_job.status == JobStatus.QUEUED:
            queued_job.status = JobStatus.CANCELED
            queued_job.error_message = "Cancelado"
            self.job_updated.emit(queued_job)
            self.log_message.emit(f"Job {job_id} canceled in queue")

    def remove_completed(self) -> None:
        self.jobs = [
            job
            for job in self.jobs
            if job.status not in {JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELED}
        ]

    def reset_running_state(self) -> None:
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait(2000)
            self._worker_thread.deleteLater()
        if self._worker:
            self._worker.deleteLater()
        self._worker_thread = None
        self._worker = None
        self._current = None
        self._is_running = False

    @QtCore.Slot(int, float, str, str)
    def _on_worker_progress(self, job_id: int, percent: float, _speed: str, _eta: str) -> None:
        job = self._find_job(job_id)
        if not job:
            return
        job.progress = max(0.0, min(100.0, percent))
        self.job_updated.emit(job)

    @QtCore.Slot(int, str)
    def _on_worker_status(self, job_id: int, status_string: str) -> None:
        job = self._find_job(job_id)
        if not job:
            return
        if status_string == JobStatus.RUNNING.value:
            job.status = JobStatus.RUNNING
        self.job_updated.emit(job)

    @QtCore.Slot(int, str, str)
    def _on_worker_metadata(self, job_id: int, title: str, _source: str) -> None:
        job = self._find_job(job_id)
        if not job:
            return
        job.title = title
        self.job_updated.emit(job)

    @QtCore.Slot(int, str)
    def _on_worker_finished(self, job_id: int, output_path: str) -> None:
        job = self._find_job(job_id)
        if job:
            job.status = JobStatus.DONE
            job.output_path = output_path
            job.progress = 100.0
            self.job_updated.emit(job)
            self.log_message.emit(f"Job {job_id} done")
        self._finalize_and_continue()

    @QtCore.Slot(int, str)
    def _on_worker_failed(self, job_id: int, error_message: str) -> None:
        job = self._find_job(job_id)
        if job:
            if error_message.lower() == "cancelado":
                job.status = JobStatus.CANCELED
            else:
                job.status = JobStatus.ERROR
            job.error_message = error_message
            self.job_updated.emit(job)
            self.log_message.emit(f"Job {job_id} {job.status.value.lower()}: {error_message}")
        self._finalize_and_continue()

    @QtCore.Slot(int, str)
    def _on_worker_log(self, _job_id: int, message: str) -> None:
        self.log_message.emit(message)

    def _finalize_and_continue(self) -> None:
        self.reset_running_state()
        QtCore.QTimer.singleShot(0, self.start_next)

    def update_options(self, options: dict) -> None:
        self.options = options

    def _find_job(self, job_id: int) -> DownloadJob | None:
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None
