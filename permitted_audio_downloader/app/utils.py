import os
import re
import sys
from pathlib import Path

INVALID_CHARS = re.compile(r"[<>:\"/\\|?*]")


def sanitize_filename(name: str, max_length: int = 120, fallback: str = "audio") -> str:
    cleaned = INVALID_CHARS.sub("", name or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = fallback
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_output_path(output_dir: str, filename: str, overwrite: bool) -> Path:
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_filename(filename)
    target = output_dir_path / f"{sanitized}.wav"
    if overwrite:
        return target
    return ensure_unique_path(target)


def get_default_music_dir() -> str:
    home = Path.home()
    return str(home / "Music" / "PermittedAudioDownloader")


def get_ffmpeg_bin_dir() -> Path | None:
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parents[1]
    bin_dir = base_dir / "assets" / "ffmpeg" / "bin"
    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    ffprobe_exe = bin_dir / "ffprobe.exe"
    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        return bin_dir
    return None
