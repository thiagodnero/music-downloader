import os
import subprocess
import sys
from pathlib import Path


class FfmpegNotFoundError(FileNotFoundError):
    pass


def _base_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def get_ffmpeg_paths() -> tuple[Path, Path]:
    base = _base_path()
    ffmpeg_path = base / "assets" / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffprobe_path = base / "assets" / "ffmpeg" / "bin" / "ffprobe.exe"
    return ffmpeg_path, ffprobe_path


def find_ffmpeg() -> str:
    ffmpeg_path, _ = get_ffmpeg_paths()
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    from shutil import which

    in_path = which("ffmpeg")
    if in_path:
        return in_path
    raise FfmpegNotFoundError(
        "ffmpeg não encontrado. Coloque o binário em assets/ffmpeg/bin ou instale no PATH."
    )


def convert_to_wav(input_path: str, output_path: str, sample_rate: int) -> None:
    ffmpeg = find_ffmpeg()
    command = [
        ffmpeg,
        "-y",
        "-i",
        input_path,
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        output_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha na conversão com ffmpeg")
