from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6 import QtCore

from . import ffmpeg_service
from .utils import resolve_output_path, sanitize_filename
from .validators import ValidationError, get_source_label, validate_url
from .ytdlp_service import download_audio


@dataclass
class DownloadItem:
    url: str
    status: str = "Na fila"
    title: str = ""
    source: str = ""
    progress: float = 0.0
    output_path: str = ""


class DownloadWorker(QtCore.QObject):
    progress_changed = QtCore.Signal(int, float)
    status_changed = QtCore.Signal(int, str)
    info_resolved = QtCore.Signal(int, str, str)
    finished = QtCore.Signal(int, bool, str)
    log = QtCore.Signal(str)

    def __init__(self, index: int, item: DownloadItem, options: dict):
        super().__init__()
        self.index = index
        self.item = item
        self.options = options
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def _check_cancelled(self) -> None:
        if self._cancelled:
            raise RuntimeError("Download cancelado")

    def _set_status(self, status: str) -> None:
        self.item.status = status
        self.status_changed.emit(self.index, status)

    def run(self) -> None:
        try:
            validate_url(self.item.url)
            self.item.source = get_source_label(self.item.url)
            self._set_status("Baixando")

            with tempfile.TemporaryDirectory() as temp_dir:
                def hook(data: dict) -> None:
                    if data.get("status") == "downloading":
                        downloaded = data.get("downloaded_bytes") or 0
                        total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                        percent = (downloaded / total * 100) if total else 0.0
                        self.progress_changed.emit(self.index, percent)
                    self._check_cancelled()

                info = download_audio(self.item.url, temp_dir, progress_callback=hook)
                self._check_cancelled()
                title = info.get("title") or "audio"
                uploader = info.get("uploader") or ""
                self.item.title = title
                self.info_resolved.emit(self.index, title, self.item.source)

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
                downloaded_path = Path(filepath)
                ffmpeg_service.convert_to_wav(
                    str(downloaded_path),
                    str(output_path),
                    self.options["sample_rate"],
                )
                self.item.output_path = str(output_path)
                self.progress_changed.emit(self.index, 100.0)
                self._set_status("Concluído")
                self.finished.emit(self.index, True, "Concluído")
        except ValidationError as exc:
            self._set_status("Falhou")
            self.finished.emit(self.index, False, str(exc))
        except Exception as exc:
            if "cancelado" in str(exc).lower():
                self._set_status("Cancelado")
                self.finished.emit(self.index, False, "Cancelado")
            else:
                self._set_status("Falhou")
                self.finished.emit(self.index, False, str(exc))


class DownloadManager(QtCore.QObject):
    item_updated = QtCore.Signal(int, DownloadItem)
    item_status = QtCore.Signal(int, str)
    item_progress = QtCore.Signal(int, float)
    item_info = QtCore.Signal(int, str, str)
    item_finished = QtCore.Signal(int, bool, str)
    log_message = QtCore.Signal(str)
    queue_empty = QtCore.Signal()

    def __init__(self, options: dict):
        super().__init__()
        self.options = options
        self.items: list[DownloadItem] = []
        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[DownloadWorker] = None

    def add_item(self, url: str) -> int:
        item = DownloadItem(url=url, source=get_source_label(url))
        self.items.append(item)
        index = len(self.items) - 1
        self.item_updated.emit(index, item)
        return index

    def start_next(self) -> None:
        if self._thread and self._thread.isRunning():
            return
        next_index = next((i for i, item in enumerate(self.items) if item.status == "Na fila"), None)
        if next_index is None:
            self.queue_empty.emit()
            return

        item = self.items[next_index]
        self._thread = QtCore.QThread()
        self._worker = DownloadWorker(next_index, item, self.options)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self.item_progress)
        self._worker.status_changed.connect(self.item_status)
        self._worker.info_resolved.connect(self.item_info)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_finished(self, index: int, success: bool, message: str) -> None:
        self.item_finished.emit(index, success, message)
        self.start_next()

    def cancel_item(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            return
        item = self.items[index]
        if item.status == "Na fila":
            item.status = "Cancelado"
            self.item_status.emit(index, "Cancelado")
            return
        if self._worker and self._worker.index == index:
            self._worker.cancel()

    def update_options(self, options: dict) -> None:
        self.options = options
