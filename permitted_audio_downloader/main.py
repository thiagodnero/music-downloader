import os
import sys

from PySide6 import QtCore, QtWidgets

from permitted_audio_downloader.app.config import load_config, save_config
from permitted_audio_downloader.app.download_manager import DownloadJob, DownloadManager, JobStatus
from permitted_audio_downloader.app.logging_setup import QtLogHandler, setup_logging
from permitted_audio_downloader.app.ui_main import UiMainWindow
from permitted_audio_downloader.app.utils import get_default_music_dir, get_ffmpeg_bin_dir
from permitted_audio_downloader.app.validators import ValidationError


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = UiMainWindow()
        self.ui.setup_ui(self)

        self.logger = setup_logging()
        self.config = load_config()
        self.ffmpeg_bin_dir = get_ffmpeg_bin_dir()
        if self.ffmpeg_bin_dir:
            os.environ["PATH"] = f"{self.ffmpeg_bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            self.logger.info("ffmpeg encontrado em: %s", self.ffmpeg_bin_dir)
        else:
            self.logger.info("ffmpeg não encontrado em assets; usando PATH do sistema (se disponível).")

        self.download_manager = DownloadManager(self._current_options())

        self._setup_ui_state()
        self._connect_signals()

        qt_handler = QtLogHandler()
        qt_handler.setFormatter(self.logger.handlers[0].formatter)
        qt_handler.log_signal.connect(self.append_log)
        self.logger.addHandler(qt_handler)

        self.logger.info("Aplicativo iniciado")

    def _setup_ui_state(self) -> None:
        self.ui.output_dir_input.setText(self.config.output_dir)
        self.ui.preserve_name_checkbox.setChecked(self.config.preserve_name)
        self.ui.overwrite_checkbox.setChecked(self.config.overwrite)
        self.ui.sample_rate_combo.setCurrentIndex(0 if self.config.sample_rate == 44100 else 1)
        self.ui.pause_button.setEnabled(False)
        self.ui.pause_button.setToolTip("Pausa não suportada no MVP")

    def _connect_signals(self) -> None:
        self.ui.add_button.clicked.connect(self.add_to_queue)
        self.ui.download_button.clicked.connect(self.start_downloads)
        self.ui.cancel_button.clicked.connect(self.cancel_selected)
        self.ui.clear_button.clicked.connect(self.clear_completed)
        self.ui.output_dir_button.clicked.connect(self.choose_output_dir)
        self.ui.output_dir_input.editingFinished.connect(self._update_config)
        self.ui.copy_logs_button.clicked.connect(self.copy_logs)

        self.download_manager.job_added.connect(self._add_table_row)
        self.download_manager.job_updated.connect(self._update_job_row)
        self.download_manager.log_message.connect(self.logger.info)

        self.ui.preserve_name_checkbox.stateChanged.connect(self._update_config)
        self.ui.overwrite_checkbox.stateChanged.connect(self._update_config)
        self.ui.sample_rate_combo.currentIndexChanged.connect(self._update_config)

    def _current_options(self) -> dict:
        return {
            "output_dir": self.config.output_dir or get_default_music_dir(),
            "preserve_name": self.config.preserve_name,
            "overwrite": self.config.overwrite,
            "sample_rate": self.config.sample_rate,
            "ffmpeg_bin_dir": self.ffmpeg_bin_dir,
        }

    def append_log(self, message: str) -> None:
        self.ui.logs_text.appendPlainText(message)

    def add_to_queue(self) -> None:
        url = self.ui.url_input.text().strip()
        try:
            job_id = self.download_manager.add_job(url)
        except ValidationError as exc:
            self.logger.warning(str(exc))
            QtWidgets.QMessageBox.warning(self, "URL inválida", str(exc))
            return
        self.ui.url_input.clear()
        self.logger.info("URL adicionada à fila no job %s", job_id)

    def start_downloads(self) -> None:
        self.download_manager.update_options(self._current_options())
        self.download_manager.start()

    def cancel_selected(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        job_id = self._job_id_from_row(row)
        if job_id is not None:
            self.download_manager.cancel(job_id)

    def clear_completed(self) -> None:
        done_status = {JobStatus.DONE.value, JobStatus.ERROR.value, JobStatus.CANCELED.value}
        for row in reversed(range(self.ui.table.rowCount())):
            status_item = self.ui.table.item(row, 0)
            if status_item and status_item.text() in done_status:
                self.ui.table.removeRow(row)
        self.download_manager.remove_completed()

    def choose_output_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Selecionar pasta",
            self.ui.output_dir_input.text() or get_default_music_dir(),
        )
        if directory:
            self.ui.output_dir_input.setText(directory)
            self.config.output_dir = directory
            save_config(self.config)

    def copy_logs(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self.ui.logs_text.toPlainText())

    def _selected_row(self) -> int | None:
        selection = self.ui.table.selectionModel().selectedRows()
        return selection[0].row() if selection else None

    def _set_job_id_on_row(self, row: int, job_id: int) -> None:
        item = self.ui.table.item(row, 0)
        if item:
            item.setData(QtCore.Qt.UserRole, job_id)

    def _job_id_from_row(self, row: int) -> int | None:
        item = self.ui.table.item(row, 0)
        if not item:
            return None
        data = item.data(QtCore.Qt.UserRole)
        return int(data) if data is not None else None

    def _find_row_for_job(self, job_id: int) -> int | None:
        for row in range(self.ui.table.rowCount()):
            if self._job_id_from_row(row) == job_id:
                return row
        return None

    def _add_table_row(self, job: DownloadJob) -> None:
        row = self.ui.table.rowCount()
        self.ui.table.insertRow(row)
        self.ui.table.setItem(row, 0, QtWidgets.QTableWidgetItem(job.status.value))
        self.ui.table.setItem(row, 1, QtWidgets.QTableWidgetItem(job.title or ""))
        self.ui.table.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
        self.ui.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{job.progress:.1f}%"))
        self.ui.table.setItem(row, 4, QtWidgets.QTableWidgetItem(job.output_path or ""))
        self._set_job_id_on_row(row, job.id)

    def _update_job_row(self, job: DownloadJob) -> None:
        row = self._find_row_for_job(job.id)
        if row is None:
            return
        status_item = self.ui.table.item(row, 0)
        title_item = self.ui.table.item(row, 1)
        source_item = self.ui.table.item(row, 2)
        progress_item = self.ui.table.item(row, 3)
        output_item = self.ui.table.item(row, 4)

        if status_item:
            status_item.setText(job.status.value)
        if title_item:
            title_item.setText(job.title or "")
        if source_item:
            source_item.setText("YT" if "youtu" in job.url.lower() else "SC")
        if progress_item:
            progress_item.setText(f"{job.progress:.1f}%")
        if output_item:
            output_item.setText(job.output_path or "")

        if job.status == JobStatus.ERROR and job.error_message:
            self.logger.error("Job %s falhou: %s", job.id, job.error_message)
        elif job.status == JobStatus.CANCELED:
            self.logger.info("Job %s cancelado", job.id)
        elif job.status == JobStatus.DONE:
            self.logger.info("Job %s concluído", job.id)

    def _update_config(self) -> None:
        self.config.preserve_name = self.ui.preserve_name_checkbox.isChecked()
        self.config.overwrite = self.ui.overwrite_checkbox.isChecked()
        self.config.sample_rate = int(self.ui.sample_rate_combo.currentText())
        output_dir = self.ui.output_dir_input.text().strip()
        self.config.output_dir = output_dir or get_default_music_dir()
        save_config(self.config)


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
