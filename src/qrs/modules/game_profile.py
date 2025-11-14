# src/qrs/modules/game_profile.py
from __future__ import annotations

"""
Game profile model for QrsTweaks (.qrsgame files).

Schema (Version 1.0):

{
  "profile_version": "1.0",
  "game_label": "Fortnite",
  "created_at": "...Z",
  "created_by": "QrsTweaks",
  "description": "Default profile for Fortnite",
  "process_names": ["FortniteClient-Win64-Shipping.exe"],
  "settings": {
    "cpu_priority": "HIGH",
    "affinity": "recommended",
    "affinity_cores": [0,1,2,3],   # optional
    "nagle": false,
    "clean_shader": true,
    "clean_logs": true,
    "clean_dx": true,
    "disable_gamebar": true,
    "disable_gamedvr": true
  }
}
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class GameProfile:
    profile_version: str
    game_label: str
    created_at: str
    created_by: str
    description: str
    process_names: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default_for_game(cls, game_label: str, process_names: List[str]) -> "GameProfile":
        """
        Build a sane default profile for a game.

        - Fortnite gets shader + log cleanup on by default
        - Other games still get DirectX cleanup + CPU priority
        """
        now = datetime.utcnow().isoformat() + "Z"
        lower = (game_label or "").strip().lower()

        is_fortnite = lower.startswith("fortnite")

        base_settings: Dict[str, Any] = {
            "cpu_priority": "HIGH",          # HIGH, ABOVE_NORMAL, NORMAL
            "affinity": "recommended",       # recommended, all, custom
            "affinity_cores": [],            # only used for custom later
            "nagle": False,                  # False = disable Nagle
            "clean_shader": bool(is_fortnite),
            "clean_logs": bool(is_fortnite),
            "clean_dx": True,
            "disable_gamebar": True,
            "disable_gamedvr": True,
        }

        return cls(
            profile_version="1.0",
            game_label=game_label,
            created_at=now,
            created_by="QrsTweaks",
            description=f"Default profile for {game_label}",
            process_names=list(process_names),
            settings=base_settings,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_version": self.profile_version,
            "game_label": self.game_label,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "description": self.description,
            "process_names": list(self.process_names),
            "settings": dict(self.settings),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameProfile":
        """
        Robust loader with fallbacks so older/future schemas don't explode.
        """
        profile_version = str(data.get("profile_version", "1.0"))
        game_label = str(data.get("game_label", "Unknown Game"))
        created_at = str(data.get("created_at", datetime.utcnow().isoformat() + "Z"))
        created_by = str(data.get("created_by", "unknown"))
        description = str(data.get("description", ""))

        process_names_raw = data.get("process_names", [])
        if not isinstance(process_names_raw, list):
            process_names: List[str] = []
        else:
            process_names = [str(x) for x in process_names_raw]

        settings_raw = data.get("settings", {})
        if not isinstance(settings_raw, dict):
            settings: Dict[str, Any] = {}
        else:
            settings = dict(settings_raw)

        # Ensure required keys exist in settings with sane defaults
        settings.setdefault("cpu_priority", "HIGH")
        settings.setdefault("affinity", "recommended")
        settings.setdefault("affinity_cores", [])
        settings.setdefault("nagle", False)
        settings.setdefault("clean_shader", False)
        settings.setdefault("clean_logs", False)
        settings.setdefault("clean_dx", True)
        settings.setdefault("disable_gamebar", True)
        settings.setdefault("disable_gamedvr", True)

        return cls(
            profile_version=profile_version,
            game_label=game_label,
            created_at=created_at,
            created_by=created_by,
            description=description,
            process_names=process_names,
            settings=settings,
        )
