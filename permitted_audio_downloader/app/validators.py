import re
from urllib.parse import urlparse

ALLOWED_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "m.youtube.com",
    "soundcloud.com",
    "www.soundcloud.com",
}

YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}
SOUNDCLOUD_DOMAINS = {"soundcloud.com", "www.soundcloud.com"}

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class ValidationError(ValueError):
    pass


def normalize_url(url: str) -> str:
    return url.strip()


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def validate_url(url: str) -> None:
    if not url or not url.strip():
        raise ValidationError("URL vazia")
    url = normalize_url(url)
    if not URL_PATTERN.match(url):
        raise ValidationError("URL inválida")
    domain = get_domain(url)
    if not domain:
        raise ValidationError("URL inválida")
    if domain not in ALLOWED_DOMAINS:
        raise ValidationError("Domínio não suportado")


def get_source_label(url: str) -> str:
    domain = get_domain(url)
    if domain in YOUTUBE_DOMAINS:
        return "YT"
    if domain in SOUNDCLOUD_DOMAINS:
        return "SC"
    return ""
