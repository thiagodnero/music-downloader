import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6 import QtCore


class QtLogHandler(QtCore.QObject, logging.Handler):
    log_signal = QtCore.Signal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.log_signal.emit(msg)
        except Exception:
            self.handleError(record)


def get_log_path() -> Path:
    appdata = os.getenv("APPDATA")
    base_dir = Path(appdata) if appdata else Path.home() / ".config"
    log_dir = base_dir / "PermittedAudioDownloader" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("permitted_audio_downloader")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    log_path = get_log_path()
    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
