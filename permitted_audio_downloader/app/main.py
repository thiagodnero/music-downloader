import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from permitted_audio_downloader.app.config import load_config, save_config
from permitted_audio_downloader.app.download_manager import DownloadManager
from permitted_audio_downloader.app.logging_setup import QtLogHandler, setup_logging
from permitted_audio_downloader.app.validators import ValidationError, validate_url
from permitted_audio_downloader.app.utils import get_default_music_dir, get_ffmpeg_bin_dir
from permitted_audio_downloader.app.ui_main import UiMainWindow


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
            self.logger.info(
                "ffmpeg não encontrado em assets; usando PATH do sistema (se disponível)."
            )

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
        index = 0 if self.config.sample_rate == 44100 else 1
        self.ui.sample_rate_combo.setCurrentIndex(index)
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

        self.download_manager.item_updated.connect(self._add_table_row)
        self.download_manager.item_status.connect(self._update_status)
        self.download_manager.item_progress.connect(self._update_progress)
        self.download_manager.item_info.connect(self._update_info)
        self.download_manager.item_finished.connect(self._handle_finished)

        self.ui.preserve_name_checkbox.stateChanged.connect(self._update_config)
        self.ui.overwrite_checkbox.stateChanged.connect(self._update_config)
        self.ui.sample_rate_combo.currentIndexChanged.connect(self._update_config)

    def _current_options(self) -> dict:
        output_dir = self.config.output_dir or get_default_music_dir()
        return {
            "output_dir": output_dir,
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
            validate_url(url)
        except ValidationError as exc:
            self.logger.warning(str(exc))
            QtWidgets.QMessageBox.warning(self, "URL inválida", str(exc))
            return
        index = self.download_manager.add_item(url)
        self.ui.url_input.clear()
        self.logger.info("URL adicionada à fila: %s", url)
        self.ui.table.selectRow(index)

    def start_downloads(self) -> None:
        self.download_manager.update_options(self._current_options())
        self.download_manager.start_next()

    def cancel_selected(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        self.download_manager.cancel_item(row)

    def clear_completed(self) -> None:
        rows_to_remove = []
        for row in range(self.ui.table.rowCount()):
            status_item = self.ui.table.item(row, 0)
            if status_item and status_item.text() in {"Concluído", "Falhou", "Cancelado"}:
                rows_to_remove.append(row)
        for row in reversed(rows_to_remove):
            self.ui.table.removeRow(row)
            del self.download_manager.items[row]

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
        if not selection:
            return None
        return selection[0].row()

    def _add_table_row(self, index: int, item) -> None:
        self.ui.table.insertRow(index)
        self.ui.table.setItem(index, 0, QtWidgets.QTableWidgetItem(item.status))
        self.ui.table.setItem(index, 1, QtWidgets.QTableWidgetItem(item.title))
        self.ui.table.setItem(index, 2, QtWidgets.QTableWidgetItem(item.source))
        self.ui.table.setItem(index, 3, QtWidgets.QTableWidgetItem("0%"))
        self.ui.table.setItem(index, 4, QtWidgets.QTableWidgetItem(item.output_path))

    def _update_status(self, index: int, status: str) -> None:
        item = self.ui.table.item(index, 0)
        if item:
            item.setText(status)

    def _update_progress(self, index: int, progress: float) -> None:
        item = self.ui.table.item(index, 3)
        if item:
            item.setText(f"{progress:.1f}%")

    def _update_info(self, index: int, title: str, source: str) -> None:
        title_item = self.ui.table.item(index, 1)
        source_item = self.ui.table.item(index, 2)
        if title_item:
            title_item.setText(title)
        if source_item:
            source_item.setText(source)

    def _handle_finished(self, index: int, success: bool, message: str) -> None:
        if not success:
            self.logger.error("Falha no item %s: %s", index + 1, message)
        else:
            self.logger.info("Item %s concluído", index + 1)
        output_item = self.ui.table.item(index, 4)
        if output_item:
            output_item.setText(self.download_manager.items[index].output_path)

    def _update_config(self) -> None:
        self.config.preserve_name = self.ui.preserve_name_checkbox.isChecked()
        self.config.overwrite = self.ui.overwrite_checkbox.isChecked()
        self.config.sample_rate = int(self.ui.sample_rate_combo.currentText())
        output_dir = self.ui.output_dir_input.text().strip()
        self.config.output_dir = output_dir or get_default_music_dir()
        save_config(self.config)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
