from __future__ import annotations

"""
src/qrs/modules/game_profile.py

Represents a per-game optimization profile for QrsTweaks.

Profiles are stored as .qrsgame JSON files and can be:
  - Built from the current UI selection (GamesPage)
  - Saved to disk
  - Loaded later and applied via GameOptimizer
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # only for type hints; avoids runtime circular import
    from src.qrs.modules.game_optim import GameOptimizer


class GameProfile:
    """
    Per-game optimization profile.

    Fields are intentionally simple for Phase 5; they can be extended later
    without breaking existing profiles.
    """

    def __init__(
        self,
        game_name: str = "",
        priority: str = "NORMAL",
        affinity: str = "recommended",
        nagle: bool = True,
        clean_temp: bool = False,
        clean_crash: bool = False,
        clean_shader: bool = False,
    ):
        self.game_name = game_name
        self.priority = (priority or "NORMAL").upper()
        self.affinity = affinity or "recommended"
        self.nagle = bool(nagle)

        self.clean_temp = bool(clean_temp)
        self.clean_crash = bool(clean_crash)
        self.clean_shader = bool(clean_shader)

    # ---------------------------------------------------
    # SERIALIZATION
    # ---------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_name": self.game_name,
            "priority": self.priority,
            "affinity": self.affinity,
            "nagle": self.nagle,
            "clean_temp": self.clean_temp,
            "clean_crash": self.clean_crash,
            "clean_shader": self.clean_shader,
            "profile_version": "1.0",
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "GameProfile":
        return GameProfile(
            game_name=data.get("game_name", ""),
            priority=data.get("priority", "NORMAL"),
            affinity=data.get("affinity", "recommended"),
            nagle=data.get("nagle", True),
            clean_temp=data.get("clean_temp", False),
            clean_crash=data.get("clean_crash", False),
            clean_shader=data.get("clean_shader", False),
        )

    # ---------------------------------------------------
    # SAVE / LOAD
    # ---------------------------------------------------
    def save(self, path: str) -> Tuple[bool, str]:
        try:
            p = Path(path)
            if p.suffix.lower() != ".qrsgame":
                # keep extension consistent
                p = p.with_suffix(".qrsgame")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            return True, f"Profile saved to {p}"
        except Exception as e:
            return False, f"Failed to save profile: {e!r}"

    @staticmethod
    def load(path: str) -> Tuple[bool, str, "GameProfile | None"]:
        p = Path(path)
        if not p.exists():
            return False, f"File not found: {p}", None

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            prof = GameProfile.from_dict(data)
            return True, f"Profile loaded from {p}", prof
        except Exception as e:
            return False, f"Failed to load profile: {e!r}", None

    # ---------------------------------------------------
    # APPLY PROFILE
    # ---------------------------------------------------
    def apply(self, optim: "GameOptimizer") -> Tuple[bool, str]:
        """
        Use GameOptimizer to apply everything in this profile.

        This is Phase 5, so we wire into the existing methods without
        trying to be 'auto-smart' yet.
        """
        logs: list[str] = []

        game = self.game_name or "<unspecified>"

        # Priority
        ok_p, msg_p = optim.apply_game_priority(game, self.priority)
        logs.append(msg_p)

        # Affinity
        if self.affinity == "recommended":
            ok_a, msg_a = optim.apply_game_affinity_recommended(game)
        elif self.affinity == "all":
            ok_a, msg_a = optim.apply_game_affinity_all_cores(game)
        else:
            ok_a, msg_a = True, f"Affinity preset '{self.affinity}' ignored (no-op)."
        logs.append(msg_a)

        # Nagle (pass-through to GameOptimizer helper)
        if self.nagle:
            ok_n, msg_n = optim.disable_nagle_for_game(game)
        else:
            ok_n, msg_n = True, "Nagle left at default setting."
        logs.append(msg_n)

        # Storage cleaners (these are best-effort)
        ok_temp = ok_crash = ok_shader = True

        if self.clean_temp:
            ok_temp, msg_t = optim.clean_game_temp(game)
            logs.append(msg_t)

        if self.clean_crash:
            ok_crash, msg_c = optim.clean_game_crashes(game)
            logs.append(msg_c)

        if self.clean_shader:
            ok_shader, msg_s = optim.clean_game_shaders(game)
            logs.append(msg_s)

        ok_all = all([ok_p, ok_a, ok_n, ok_temp, ok_crash, ok_shader])
        return ok_all, "\n".join(logs)
