import pytest

from permitted_audio_downloader.app.validators import ValidationError, validate_url


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com/watch?v=abc",
        "https://www.youtube.com/watch?v=abc",
        "https://youtu.be/abc",
        "https://m.youtube.com/watch?v=abc",
        "https://soundcloud.com/artist/track",
        "https://www.soundcloud.com/artist/track",
    ],
)
def test_validate_url_allows_domains(url):
    validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "youtube.com/watch?v=abc",
        "https://example.com/track",
    ],
)
def test_validate_url_rejects_invalid(url):
    with pytest.raises(ValidationError):
        validate_url(url)
