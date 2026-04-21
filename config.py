import tomllib
from pathlib import Path


def get_config_path() -> Path:
    return Path() / "config.toml"


def load_or_create_config(default_app_data: str) -> dict:
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    config_path.write_text(f'app_data_path = "{default_app_data}"\n', encoding="utf-8")
    return {"app_data_path": default_app_data}


def get_app_data_path(config: dict) -> Path:
    return Path(config["app_data_path"]).expanduser()
