from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from yt_dlp import YoutubeDL

ProgressCallback = Callable[[dict[str, Any]], None]


def download_audio(
    url: str,
    temp_dir: str,
    progress_callback: ProgressCallback | None = None,
    ffmpeg_location: Path | None = None,
) -> dict[str, Any]:
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    def hook(data: dict[str, Any]) -> None:
        if progress_callback:
            progress_callback(data)

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [hook],
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = str(ffmpeg_location)

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return info
