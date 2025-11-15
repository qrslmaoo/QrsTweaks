# src/qrs/modules/game_profile.py

from __future__ import annotations

"""
Game profile backend for QrsTweaks.

Handles:
- Loading *.qrsgame JSON files
- Normalizing action tokens
- Saving profiles
- Applying profiles through a GameOptimizer instance (passed in at runtime)

IMPORTANT:
This module intentionally does NOT import GameOptimizer to avoid circular imports.
The GamesPage or caller must pass an already-constructed GameOptimizer.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class GameProfile:
    name: str
    game_label: str
    actions: List[str]
    description: str = ""
    schema: str = "qrs.gameprofile/v1"
    source_path: Optional[Path] = None


# ------------------------------------------------------------
# Action normalization
# ------------------------------------------------------------

def _normalize_actions(raw) -> List[str]:
    if not isinstance(raw, list):
        return []

    out: List[str] = []
    for entry in raw:
        if isinstance(entry, str):
            t = entry.strip()
            if t:
                out.append(t)
            continue

        if isinstance(entry, dict):
            token = (
                entry.get("type")
                or entry.get("action")
                or ""
            )
            token = str(token).strip()
            if not token:
                continue

            level = entry.get("level") or entry.get("preset")
            if level:
                token = f"{token}:{str(level).strip()}"

            out.append(token)

    return out


# ------------------------------------------------------------
# Loading
# ------------------------------------------------------------

def load_game_profile(path: str | Path) -> Tuple[bool, str, Optional[GameProfile]]:
    p = Path(path)
    if not p.exists():
        return False, f"[Profile] File not found: {p}", None

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"[Profile] Failed to parse JSON: {e!r}", None

    name = str(data.get("name") or data.get("profile_name") or p.stem)
    game_label = str(
        data.get("game_label")
        or data.get("game")
        or data.get("title")
        or "Unknown"
    )

    description = str(data.get("description") or data.get("notes") or "")
    schema = str(data.get("schema") or "qrs.gameprofile/v1")

    raw_actions = (
        data.get("actions")
        or data.get("steps")
        or data.get("action_list")
        or []
    )
    actions = _normalize_actions(raw_actions)

    profile = GameProfile(
        name=name,
        game_label=game_label,
        actions=actions,
        description=description,
        schema=schema,
        source_path=p,
    )

    if not actions:
        return False, f"[Profile] Loaded '{name}' but it contains no actions.", profile

    return True, f"[Profile] Loaded '{name}' for game '{game_label}'.", profile


# ------------------------------------------------------------
# Saving
# ------------------------------------------------------------

def save_game_profile(path: str | Path, profile: GameProfile) -> Tuple[bool, str]:
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"[Profile] Failed to create folder {p.parent}: {e!r}"

    data = {
        "schema": profile.schema,
        "name": profile.name,
        "game_label": profile.game_label,
        "description": profile.description,
        "actions": list(profile.actions),
    }

    try:
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True, f"[Profile] Saved to {p}"
    except Exception as e:
        return False, f"[Profile] Failed to write {p}: {e!r}"


# ------------------------------------------------------------
# Action Router (NO GAMEOPTIM IMPORT)
# GameOptimizer is passed as `opt`
# ------------------------------------------------------------

def _apply_action_token(token: str, game_label: str, opt) -> Tuple[bool, str]:
    t_raw = (token or "").strip()
    if not t_raw:
        return False, "Empty token."

    # Parse optional suffix
    if ":" in t_raw:
        base, suffix = t_raw.split(":", 1)
        base = base.strip().lower()
        suffix = suffix.strip().upper()
    else:
        base = t_raw.strip().lower()
        suffix = ""

    # Fortnite cleanups
    if base in ("fortnite.clean_logs", "fn.clean_logs", "fortnite.logs"):
        return opt.clean_fortnite_logs_and_crashes()

    if base in ("fortnite.clean_shaders", "fn.clean_shaders", "fortnite.shaders"):
        return opt.clean_fortnite_shader_cache()

    # DirectX cache
    if base in ("dx.clean_cache", "directx.clean", "directx.clean_cache"):
        return opt.clean_directx_cache()

    # Game Bar / DVR
    if base in ("os.disable_gamebar", "xbox.disable_gamebar", "game.disable_gamebar"):
        return opt.disable_xbox_game_bar()

    if base in ("os.disable_dvr", "xbox.disable_dvr", "game.disable_dvr"):
        return opt.disable_game_dvr()

    # CPU priority
    if base in ("cpu.priority", "game.cpu.priority", "priority"):
        level = suffix or "HIGH"
        return opt.apply_game_priority(game_label, level)

    if base in ("cpu.priority.high",):
        return opt.apply_game_priority(game_label, "HIGH")

    if base in ("cpu.priority.above", "cpu.priority.above_normal"):
        return opt.apply_game_priority(game_label, "ABOVE_NORMAL")

    # CPU affinity
    if base in ("cpu.affinity.recommended",):
        return opt.apply_game_affinity_recommended(game_label)

    if base in ("cpu.affinity.all", "cpu.affinity.reset"):
        return opt.apply_game_affinity_all_cores(game_label)

    # Composite / presets
    if base in ("preset.fortnite.gaming",):
        return opt.apply_fortnite_gaming_preset()

    return False, f"Unknown action token: '{token}'"


# ------------------------------------------------------------
# Apply a full profile
# ------------------------------------------------------------

def apply_game_profile(
    profile: GameProfile,
    game_label: Optional[str],
    opt,
) -> Tuple[bool, str]:
    effective_label = (game_label or profile.game_label).strip()

    logs: List[str] = []
    all_ok = True

    for token in profile.actions:
        ok, msg = _apply_action_token(token, effective_label, opt)
        logs.append(f"[{'OK' if ok else 'WARN'}] {token} → {msg}")
        all_ok = all_ok and ok

    header = f"[Profile] Applied '{profile.name}' to '{effective_label}'."
    return all_ok, header + "\n" + "\n".join(logs)
