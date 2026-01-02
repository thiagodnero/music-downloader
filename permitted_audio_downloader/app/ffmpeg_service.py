import subprocess
from pathlib import Path


from permitted_audio_downloader.app.utils import get_ffmpeg_bin_dir


class FfmpegNotFoundError(FileNotFoundError):
    pass


def find_ffmpeg() -> str:
    bin_dir = get_ffmpeg_bin_dir()
    if bin_dir:
        return str(bin_dir / "ffmpeg.exe")
    from shutil import which

    in_path = which("ffmpeg")
    if in_path:
        return in_path
    raise FfmpegNotFoundError(
        "ffmpeg não encontrado. Coloque ffmpeg.exe e ffprobe.exe em "
        "permitted_audio_downloader/assets/ffmpeg/bin ou instale no PATH."
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
