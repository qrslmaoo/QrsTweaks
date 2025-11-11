from __future__ import annotations
import json
from pathlib import Path
from .paths import config_dir

_DEFAULT = {
    "version": "0.0.1",
    "telemetry": False,   # stays False forever (offline)
    "ui": {"theme": "dark"}
}

class Config:
    def __init__(self, path: Path | None = None):
        self.path = path or (config_dir() / "config.json")
        self.data = dict(_DEFAULT)
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except Exception:
                pass

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
