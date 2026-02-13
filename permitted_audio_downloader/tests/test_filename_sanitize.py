from permitted_audio_downloader.app.utils import sanitize_filename


def test_sanitize_removes_invalid_chars():
    name = 'Artist: "Track" <>?*'
    assert sanitize_filename(name) == "Artist Track"


def test_sanitize_limits_length():
    name = "a" * 200
    assert len(sanitize_filename(name, max_length=120)) == 120


def test_sanitize_fallback():
    assert sanitize_filename("   ") == "audio"
