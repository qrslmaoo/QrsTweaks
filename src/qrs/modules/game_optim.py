from __future__ import annotations
import json
from pathlib import Path

class GameOptimizer:
    def __init__(self, profiles_dir: Path):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self):
        return [p.stem for p in self.profiles_dir.glob("*.json")]

    def load_profile(self, name: str) -> dict:
        path = self.profiles_dir / f"{name}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def apply_profile(self, name: str):
        data = self.load_profile(name)
        if not data:
            return False, "Profile not found."
        # Stub: show what we'd do. Later you can implement file edits/ini tweaks.
        actions = data.get("actions", [])
        # Here you could expand to actually modify config files per action.
        return True, f"Applied {len(actions)} actions from profile '{name}'."
