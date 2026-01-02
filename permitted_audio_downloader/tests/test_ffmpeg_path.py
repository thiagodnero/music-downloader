from pathlib import Path

from permitted_audio_downloader.app.utils import get_ffmpeg_bin_dir


def test_get_ffmpeg_bin_dir_dev(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    bin_dir = repo_root / "permitted_audio_downloader" / "assets" / "ffmpeg" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    ffprobe_exe = bin_dir / "ffprobe.exe"
    ffmpeg_exe.write_text("")
    ffprobe_exe.write_text("")

    try:
        resolved = get_ffmpeg_bin_dir()
        assert resolved == bin_dir
    finally:
        ffmpeg_exe.unlink(missing_ok=True)
        ffprobe_exe.unlink(missing_ok=True)
