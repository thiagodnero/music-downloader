import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

from .utils import get_default_music_dir


@dataclass
class AppConfig:
    output_dir: str
    preserve_name: bool
    overwrite: bool
    sample_rate: int


DEFAULT_CONFIG = AppConfig(
    output_dir=get_default_music_dir(),
    preserve_name=True,
    overwrite=False,
    sample_rate=44100,
)


def get_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    base_dir = Path(appdata) if appdata else Path.home() / ".config"
    config_dir = base_dir / "PermittedAudioDownloader"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> AppConfig:
    path = get_config_path()
    if not path.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppConfig(
            output_dir=data.get("output_dir", DEFAULT_CONFIG.output_dir),
            preserve_name=bool(data.get("preserve_name", DEFAULT_CONFIG.preserve_name)),
            overwrite=bool(data.get("overwrite", DEFAULT_CONFIG.overwrite)),
            sample_rate=int(data.get("sample_rate", DEFAULT_CONFIG.sample_rate)),
        )
    except (json.JSONDecodeError, OSError, ValueError):
        return DEFAULT_CONFIG


def save_config(config: AppConfig) -> None:
    path = get_config_path()
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
