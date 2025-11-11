from pathlib import Path
import os

_APP_DIR = Path.home() / ".qrs"
_DATA_DIR = _APP_DIR / "data"
_CFG_DIR  = _APP_DIR / "config"

def ensure_app_dirs():
    _APP_DIR.mkdir(parents=True, exist_ok=True)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _CFG_DIR.mkdir(parents=True, exist_ok=True)

def app_dir() -> Path:
    return _APP_DIR

def data_dir() -> Path:
    return _DATA_DIR

def config_dir() -> Path:
    return _CFG_DIR
