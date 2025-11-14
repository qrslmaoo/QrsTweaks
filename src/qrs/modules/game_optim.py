from __future__ import annotations

"""
src/qrs/modules/game_optim.py

Backend logic for per-game optimization.

This module focuses on *game-scoped* tweaks and cleanups, separate from the
global Windows optimizer. It currently includes:

- Xbox Game Bar / Game DVR toggles (for reducing recording overhead)
- Fortnite-specific cache + log cleanup
- DirectX shader cache cleanup
- Process detection engine (Phase 4A)
- Per-game CPU priority & CPU affinity helpers (Phase 4B)
- Game Profiles v2 (.qrsgame) with schema v1.0

Everything here is designed to be **safe by default**:
- Only touches known game directories or well-known cache locations
- Fails gracefully on non-Windows systems
"""

import json
import os
import shutil
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, NamedTuple, List, Optional

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional
    psutil = None

from .game_profile import GameProfile


class ProcessInfo(NamedTuple):
    pid: int
    name: str


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _run_shell(cmd: str) -> Tuple[bool, str]:
    """
    Run a command through the shell and return (ok, combined_output).
    Never raises, always returns a string.
    """
    try:
        cp = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )
        out = (cp.stdout or "") + (cp.stderr or "")
        out = out.strip()
        return (cp.returncode == 0, out or f"(exit {cp.returncode})")
    except Exception as e:  # pragma: no cover - extremely defensive
        return False, f"Exception while running command: {e!r}"


class GameOptimizer:
    """
    Core logic class for per-game optimizations.

    UI integration:
      - app/pages/games_page.py instantiates this and calls methods like:
            disable_xbox_game_bar()
            disable_game_dvr()
            clean_fortnite_shader_cache()
            clean_fortnite_logs_and_crashes()
            clean_directx_cache()
            apply_game_priority(...)
            apply_game_affinity_recommended(...)
            apply_game_affinity_all_cores(...)
            apply_profile_for_game(...)
            export_profile_to_file(...)
            import_profile_from_file(...)
    """

    def __init__(self) -> None:
        # Profiles live under: <project_root>/profiles/games/*.qrsgame
        self.root = Path.cwd()
        self.profiles_dir = self.root / "profiles" / "games"
        try:
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Non-fatal; we will error at write-time instead
            pass

    # =========================================================
    #   XBOX GAME BAR / DVR
    # =========================================================

    def disable_xbox_game_bar(self) -> Tuple[bool, str]:
        """
        Disable Xbox Game Bar overlay and capture via registry toggles.
        Works only on Windows; otherwise returns (False, reason).
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak Game Bar."

        cmds = [
            # Turn off Game Bar UI
            r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
        ]

        logs = []
        ok_all = True
        for c in cmds:
            ok, out = _run_shell(c)
            ok_all = ok_all and ok
            logs.append(f"$ {c}\n{out}")

        msg = "Xbox Game Bar disabled.\n" + "\n\n".join(logs)
        return ok_all, msg

    def disable_game_dvr(self) -> Tuple[bool, str]:
        """
        Disable background Game DVR recording.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak Game DVR."

        cmds = [
            # DSE behavior & AllowGameDVR flags
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_DSEBehavior /t REG_DWORD /d 2 /f',
            r'reg add "HKCU\System\GameConfigStore" /v AllowGameDVR /t REG_DWORD /d 0 /f',
        ]

        logs = []
        ok_all = True
        for c in cmds:
            ok, out = _run_shell(c)
            ok_all = ok_all and ok
            logs.append(f"$ {c}\n{out}")

        msg = "Game DVR disabled.\n" + "\n\n".join(logs)
        return ok_all, msg

    # =========================================================
    #   FORTNITE-SPECIFIC CLEANUPS
    # =========================================================

    def _fortnite_paths(self) -> Dict[str, Path]:
        """
        Returns key paths used for Fortnite cleanup, rooted under:
            %LOCALAPPDATA%/FortniteGame/Saved

        Keys:
            base      -> Saved root
            logs      -> Saved/Logs
            crashes   -> Saved/Crashes
            shaders   -> Saved/ShaderCaches (approximate)
        """
        lad = os.environ.get("LOCALAPPDATA")
        if not lad:
            # Return placeholders that clearly show the environment issue
            dummy = Path("LOCALAPPDATA_NOT_SET")
            return {
                "base": dummy,
                "logs": dummy / "Logs",
                "crashes": dummy / "Crashes",
                "shaders": dummy / "ShaderCaches",
            }

        base = Path(lad) / "FortniteGame" / "Saved"
        return {
            "base": base,
            "logs": base / "Logs",
            "crashes": base / "Crashes",
            "shaders": base / "ShaderCaches",
        }

    def _delete_dir_contents(self, p: Path) -> int:
        """
        Delete direct children of directory `p` (files + subdirs).
        Does NOT delete `p` itself.

        Returns approximate number of items removed.
        """
        if not p.exists() or not p.is_dir():
            return 0

        count = 0
        for child in p.iterdir():
            try:
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    if child.exists():
                        child.unlink()
                count += 1
            except Exception:
                # Best-effort only; permission issues are ignored
                continue
        return count

    def clean_fortnite_shader_cache(self) -> Tuple[bool, str]:
        """
        Clean Fortnite shader / pipeline caches under:
            %LOCALAPPDATA%/FortniteGame/Saved/ShaderCaches
        """
        paths = self._fortnite_paths()
        shaders = paths["shaders"]

        removed = self._delete_dir_contents(shaders)
        if removed == 0:
            return False, f"No shader cache entries removed (directory missing or empty: {shaders})"

        return True, f"Removed ~{removed} Fortnite shader cache entries from {shaders}"

    def clean_fortnite_logs_and_crashes(self) -> Tuple[bool, str]:
        """
        Delete Fortnite logs and crash dumps under:
            %LOCALAPPDATA%/FortniteGame/Saved/Logs
            %LOCALAPPDATA%/FortniteGame/Saved/Crashes
        """
        paths = self._fortnite_paths()
        logs_dir = paths["logs"]
        crash_dir = paths["crashes"]

        removed_logs = self._delete_dir_contents(logs_dir)
        removed_crashes = self._delete_dir_contents(crash_dir)

        ok = (removed_logs + removed_crashes) > 0
        msg = (
            f"Fortnite logs removed: ~{removed_logs} from {logs_dir}\n"
            f"Fortnite crashes removed: ~{removed_crashes} from {crash_dir}"
        )
        return ok, msg

    # =========================================================
    #   DIRECTX CACHE CLEANUP
    # =========================================================

    def clean_directx_cache(self) -> Tuple[bool, str]:
        """
        Clean DirectX cache under LOCALAPPDATA\\D3DSCache and a few
        other known, safe locations.

        This is a *global* graphics cache, but games like Fortnite can
        benefit from periodically clearing it.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot clean DirectX cache."

        lad = os.environ.get("LOCALAPPDATA")
        if not lad:
            return False, "LOCALAPPDATA not found; cannot clean DirectX cache."

        base = Path(lad)
        # Focus on the standard D3DSCache directory. We avoid touching
        # obscure GPU-driver-specific directories here on purpose.
        targets = [
            base / "D3DSCache",
        ]

        total_removed = 0
        details: List[str] = []

        for t in targets:
            removed = self._delete_dir_contents(t)
            total_removed += removed
            details.append(f"{t} -> ~{removed} entries removed.")

        ok = total_removed > 0
        msg = "DirectX cache cleanup complete.\n" + "\n".join(details)
        return ok, msg

    # =========================================================
    #   COMPOSED PRESET EXAMPLE (FORTNITE "GAMING" PRESET)
    # =========================================================

    def apply_fortnite_gaming_preset(self) -> Tuple[bool, str]:
        """
        Example helper that wires together:
          - Disable Game Bar
          - Disable Game DVR
          - Clean Fortnite shader cache
          - Clean Fortnite logs/crashes
          - Clean DirectX cache
        """
        steps: List[Tuple[str, bool, str]] = []

        ok_gb, msg_gb = self.disable_xbox_game_bar()
        steps.append(("Game Bar", ok_gb, msg_gb))

        ok_dvr, msg_dvr = self.disable_game_dvr()
        steps.append(("Game DVR", ok_dvr, msg_dvr))

        ok_sh, msg_sh = self.clean_fortnite_shader_cache()
        steps.append(("Shader Cache", ok_sh, msg_sh))

        ok_logs, msg_logs = self.clean_fortnite_logs_and_crashes()
        steps.append(("Logs/Crashes", ok_logs, msg_logs))

        ok_dx, msg_dx = self.clean_directx_cache()
        steps.append(("DirectX Cache", ok_dx, msg_dx))

        ok_all = all(s[1] for s in steps)
        lines = []
        for label, ok, msg in steps:
            state = "OK" if ok else "WARN"
            lines.append(f"[{state}] {label}: {msg}")

        return ok_all, "\n".join(lines)

    # =========================================================
    #   PROCESS DETECTION ENGINE (Phase 4A)
    # =========================================================
    #
    # This layer is used by:
    #   - Per-game CPU priority tweaks
    #   - Per-game Nagle / latency presets
    #   - Any "while game is running" features
    #
    # It does NOT auto-scan or permanently monitor anything;
    # it only looks for processes when explicitly called.

    def _game_to_process_names(self, game_label: str) -> list[str]:
        """
        Map a friendly game label (from the UI combo) to one or more
        plausible process names.

        The labels are defined in app/pages/games_page.py:
            "Fortnite", "Minecraft", "Valorant", "Call of Duty", "Custom Game…"
        """
        label = (game_label or "").strip().lower()

        if label.startswith("fortnite"):
            return ["FortniteClient-Win64-Shipping.exe"]
        if label.startswith("minecraft"):
            # Java + Windows edition
            return ["javaw.exe", "Minecraft.Windows.exe"]
        if label.startswith("valorant"):
            return ["VALORANT-Win64-Shipping.exe"]
        if label.startswith("call of duty") or label.startswith("cod"):
            # CoD has many variants; keep it generic for now
            return [
                "cod.exe",
                "cod16.exe",
                "cod17.exe",
                "cod18.exe",
                "modernwarfare.exe",
                "mw2.exe",
                "mw3.exe",
            ]
        # Custom game: we don't guess; UI can later prompt for name
        return []

    def _is_psutil_ready(self) -> Tuple[bool, str]:
        """
        Small guard to avoid hard-crashing when psutil is missing or
        platform is not supported.
        """
        if not _is_windows():
            return False, "Process detection is only supported on Windows."
        if psutil is None:
            return False, "psutil is not installed; install with `pip install psutil`."
        return True, ""

    def _iter_candidate_processes(self, names: list[str]) -> list[ProcessInfo]:
        """
        Return a list of matching processes for any of the given exe names.
        Chooses by comparing case-insensitive process.name().
        """
        ok, _ = self._is_psutil_ready()
        if not ok or not names:
            return []

        wanted = {n.lower() for n in names}
        found: list[ProcessInfo] = []

        try:
            for p in psutil.process_iter(["pid", "name"]):  # type: ignore[attr-defined]
                try:
                    name = (p.info.get("name") or "").strip()
                    if not name:
                        continue
                    if name.lower() in wanted:
                        found.append(ProcessInfo(pid=p.info["pid"], name=name))
                except (psutil.NoSuchProcess, psutil.AccessDenied):  # type: ignore[attr-defined]
                    continue
        except Exception:
            # Anything weird from psutil, just treat as "no processes"
            return []

        return found

    def find_game_process(
        self,
        game_label: str,
        timeout_sec: float = 0.0,
        poll_interval: float = 1.0,
    ) -> Tuple[bool, str, ProcessInfo | None]:
        """
        Core entry for the rest of the optimizer.

        Args:
            game_label: Text shown in the Game combobox
            timeout_sec: How long to wait for the game to appear
                         0 = no waiting, just one scan
            poll_interval: How often to recheck while waiting

        Returns:
            (ok, message, ProcessInfo or None)

        Examples of 'ok':
            True,  "Found FortniteClient-Win64-Shipping.exe (PID 1234)", ProcessInfo(...)
            False, "No matching process found for Fortnite", None
        """
        ok, msg = self._is_psutil_ready()
        if not ok:
            return False, msg, None

        target_names = self._game_to_process_names(game_label)
        if not target_names:
            return False, f"No known process mapping for '{game_label}'.", None

        import time as _time

        deadline = _time.time() + max(timeout_sec, 0.0)
        attempt = 0

        while True:
            attempt += 1
            matches = self._iter_candidate_processes(target_names)
            if matches:
                # Prefer the one with the highest memory usage if we can
                best = matches[0]
                try:
                    if psutil is not None:
                        best_proc = max(
                            (psutil.Process(m.pid) for m in matches),  # type: ignore[attr-defined]
                            key=lambda p: p.memory_info().rss,
                        )
                        best = ProcessInfo(pid=best_proc.pid, name=best_proc.name())
                except Exception:
                    best = matches[0]

                return (
                    True,
                    f"Found {best.name} (PID {best.pid}) after {attempt} scan(s).",
                    best,
                )

            if _time.time() >= deadline or timeout_sec <= 0:
                pretty = ", ".join(target_names)
                return False, f"No running process found for {game_label} ({pretty}).", None

            _time.sleep(max(poll_interval, 0.1))

    def wait_for_game(
        self,
        game_label: str,
        timeout_sec: float = 30.0,
    ) -> Tuple[bool, str, ProcessInfo | None]:
        """
        High-level helper: wait up to timeout_sec for the game to appear.

        Intended use:
            ok, msg, proc = self.wait_for_game("Fortnite", timeout_sec=60)
            if ok:
                # bump priority, tweak network, etc.
        """
        return self.find_game_process(
            game_label=game_label,
            timeout_sec=timeout_sec,
            poll_interval=1.0,
        )

    def get_game_pid_or_none(self, game_label: str) -> int | None:
        """
        Single-shot: return a PID for the selected game if it's running,
        or None if not.

        No waiting, no retries.
        """
        ok, _, proc = self.find_game_process(
            game_label=game_label,
            timeout_sec=0.0,
            poll_interval=0.5,
        )
        return proc.pid if ok and proc is not None else None

    # =========================================================
    #   CPU PRIORITY & AFFINITY (Phase 4B)
    # =========================================================

    def set_process_priority(self, pid: int, level: str) -> Tuple[bool, str]:
        """
        Set priority of a process by PID using psutil.

        Levels (case-insensitive):
            "HIGH"
            "ABOVE_NORMAL"
            "NORMAL" (fallback)
        """
        ok, msg = self._is_psutil_ready()
        if not ok:
            return False, msg
        if not _is_windows():
            return False, "CPU priority changes are only supported on Windows."

        assert psutil is not None  # for type checkers
        try:
            proc = psutil.Process(pid)  # type: ignore[attr-defined]
            lvl = (level or "").upper()

            if lvl == "HIGH":
                priority = psutil.HIGH_PRIORITY_CLASS  # type: ignore[attr-defined]
            elif lvl in ("ABOVE_NORMAL", "ABOVE"):
                priority = psutil.ABOVE_NORMAL_PRIORITY_CLASS  # type: ignore[attr-defined]
            else:
                priority = psutil.NORMAL_PRIORITY_CLASS  # type: ignore[attr-defined]

            proc.nice(priority)  # type: ignore[arg-type]
            return True, f"Priority set to {lvl} for PID {pid}."
        except Exception as e:
            return False, f"Failed to set priority for PID {pid}: {e!r}"

    def apply_game_priority(self, game_label: str, level: str) -> Tuple[bool, str]:
        """
        Resolve game → PID, then apply process priority.
        """
        pid = self.get_game_pid_or_none(game_label)
        if pid is None:
            return False, f"No running process found for '{game_label}'. Launch the game first."

        ok, msg = self.set_process_priority(pid, level)
        if ok:
            return True, f"{msg} (game='{game_label}')"
        return False, msg

    def _recommended_gaming_cores(self) -> List[int]:
        """
        Compute a 'recommended' gaming core set.

        Strategy:
          - Use up to the first 8 logical cores.
          - If fewer than 8 cores exist, use all.
        """
        ok, _ = self._is_psutil_ready()
        if not ok or psutil is None:
            return []

        try:
            total = psutil.cpu_count(logical=True) or 0  # type: ignore[attr-defined]
        except Exception:
            total = 0

        if total <= 0:
            return []

        use = min(8, total)
        return list(range(use))

    def set_cpu_affinity(self, pid: int, cores: List[int]) -> Tuple[bool, str]:
        """
        Apply CPU affinity to a PID using psutil.

        cores: list of logical CPU indices, e.g. [0,1,2,3].
        """
        ok, msg = self._is_psutil_ready()
        if not ok:
            return False, msg
        if not _is_windows():
            return False, "CPU affinity tweaks are only supported on Windows."

        if not cores:
            return False, "No cores specified for affinity."

        assert psutil is not None  # for type checkers
        try:
            proc = psutil.Process(pid)  # type: ignore[attr-defined]
            proc.cpu_affinity(cores)    # type: ignore[attr-defined]
            return True, f"Affinity set to cores={cores} for PID {pid}."
        except Exception as e:
            return False, f"Failed to set CPU affinity for PID {pid}: {e!r}"

    def apply_game_affinity_recommended(self, game_label: str) -> Tuple[bool, str]:
        """
        Bind the game to a recommended subset of high-performance cores.
        """
        pid = self.get_game_pid_or_none(game_label)
        if pid is None:
            return False, f"No running process found for '{game_label}'. Launch the game first."

        cores = self._recommended_gaming_cores()
        if not cores:
            return False, "Could not determine recommended cores; psutil / CPU info unavailable."

        ok, msg = self.set_cpu_affinity(pid, cores)
        if ok:
            return True, f"{msg} (game='{game_label}', preset='recommended')"
        return False, msg

    def apply_game_affinity_all_cores(self, game_label: str) -> Tuple[bool, str]:
        """
        Bind the game to all logical cores (removes previous restrictions).
        """
        ok, _ = self._is_psutil_ready()
        if not ok or psutil is None:
            return False, "psutil not available or platform unsupported."

        pid = self.get_game_pid_or_none(game_label)
        if pid is None:
            return False, f"No running process found for '{game_label}'. Launch the game first."

        try:
            total = psutil.cpu_count(logical=True) or 0  # type: ignore[attr-defined]
        except Exception:
            total = 0

        if total <= 0:
            return False, "Could not determine CPU core count."

        cores = list(range(total))
        ok2, msg = self.set_cpu_affinity(pid, cores)
        if ok2:
            return True, f"{msg} (game='{game_label}', preset='all cores')"
        return False, msg

    # =========================================================
    #   GAME PROFILES V2 (.qrsgame)
    # =========================================================

    def _profile_slug(self, game_label: str) -> str:
        label = (game_label or "").strip().lower()
        if not label:
            label = "unknown"
        # Strip unicode ellipsis and dots, normalize spaces
        label = label.replace("…", "")
        label = label.replace("...", "")
        slug = label.replace(" ", "_")
        return slug

    def _profile_default_path(self, game_label: str) -> Path:
        slug = self._profile_slug(game_label)
        return self.profiles_dir / f"{slug}.qrsgame"

    def build_default_profile(self, game_label: str) -> GameProfile:
        names = self._game_to_process_names(game_label)
        return GameProfile.default_for_game(game_label, names)

    def load_profile_for_game(self, game_label: str) -> Tuple[bool, str, GameProfile]:
        """
        Load profile from profiles/games/*.qrsgame.

        Returns:
            (has_file, message, GameProfile)
            - has_file = True if a real file existed
            - if no file or error, returns a default profile instead
        """
        path = self._profile_default_path(game_label)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                profile = GameProfile.from_dict(data)
                return True, f"Loaded profile from {path}", profile
            except Exception as e:
                profile = self.build_default_profile(game_label)
                return False, f"Failed to load profile at {path}, using defaults: {e!r}", profile
        else:
            profile = self.build_default_profile(game_label)
            return False, f"No saved profile for {game_label}; using built-in defaults.", profile

    def save_profile_for_game(self, game_label: str) -> Tuple[bool, str]:
        """
        Save the current default profile for a game to its default path.
        """
        _, _, profile = self.load_profile_for_game(game_label)
        path = self._profile_default_path(game_label)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
            return True, f"Profile for {game_label} saved to {path}"
        except Exception as e:
            return False, f"Failed to save profile for {game_label}: {e!r}"

    def export_profile_to_file(self, game_label: str, path: str) -> Tuple[bool, str]:
        """
        Export a game profile (default or saved) to an arbitrary .qrsgame path.
        """
        _, _, profile = self.load_profile_for_game(game_label)
        out = Path(path)
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
            return True, f"Profile for {game_label} exported to {out}"
        except Exception as e:
            return False, f"Failed to export profile for {game_label}: {e!r}"

    def import_profile_from_file(
        self,
        path: str,
        game_label_override: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Import a .qrsgame profile and store it as the default profile for
        the given game.

        If game_label_override is provided, it forces the label used for
        storage regardless of what's inside the file.
        """
        src = Path(path)
        if not src.exists():
            return False, f"Profile file not found: {src}"

        try:
            data = json.loads(src.read_text(encoding="utf-8"))
            profile = GameProfile.from_dict(data)
        except Exception as e:
            return False, f"Failed to read profile from {src}: {e!r}"

        if game_label_override:
            profile.game_label = game_label_override

        dst = self._profile_default_path(profile.game_label)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")
            return True, f"Imported profile for {profile.game_label} into {dst}"
        except Exception as e:
            return False, f"Failed to import profile into {dst}: {e!r}"

    def apply_profile_for_game(self, game_label: str) -> Tuple[bool, str]:
        """
        Core entry used by UI + daemon.

        Steps:
          - Load profile (or build default)
          - Apply:
              * Game Bar / DVR flags
              * Fortnite-specific cleanups (if Fortnite)
              * DirectX cache cleanup
              * CPU priority
              * CPU affinity
              * (future) Nagle per-game
        """
        has_file, msg_load, profile = self.load_profile_for_game(game_label)
        lines: List[str] = []
        lines.append(msg_load)

        overall_ok = True
        settings = profile.settings or {}
        label_lower = profile.game_label.strip().lower()

        # 1) Toggle Game Bar / DVR
        if settings.get("disable_gamebar", True):
            ok, msg = self.disable_xbox_game_bar()
            overall_ok = overall_ok and ok
            lines.append(f"[GameBar] {msg}")

        if settings.get("disable_gamedvr", True):
            ok, msg = self.disable_game_dvr()
            overall_ok = overall_ok and ok
            lines.append(f"[GameDVR] {msg}")

        # 2) Fortnite-specific cleanup
        is_fortnite = label_lower.startswith("fortnite")
        if is_fortnite and settings.get("clean_shader", True):
            ok, msg = self.clean_fortnite_shader_cache()
            overall_ok = overall_ok and ok
            lines.append(f"[Fortnite/Shader] {msg}")

        if is_fortnite and settings.get("clean_logs", True):
            ok, msg = self.clean_fortnite_logs_and_crashes()
            overall_ok = overall_ok and ok
            lines.append(f"[Fortnite/Logs] {msg}")

        # 3) DirectX cache cleanup (global)
        if settings.get("clean_dx", True):
            ok, msg = self.clean_directx_cache()
            overall_ok = overall_ok and ok
            lines.append(f"[DirectX] {msg}")

        # 4) CPU priority
        priority = str(settings.get("cpu_priority", "HIGH"))
        ok_prio, msg_prio = self.apply_game_priority(profile.game_label, priority)
        overall_ok = overall_ok and ok_prio
        lines.append(f"[CPU] {msg_prio}")

        # 5) CPU affinity
        affinity = str(settings.get("affinity", "recommended")).lower()
        if affinity == "recommended":
            ok_aff, msg_aff = self.apply_game_affinity_recommended(profile.game_label)
            overall_ok = overall_ok and ok_aff
            lines.append(f"[Affinity] {msg_aff}")
        elif affinity == "all":
            ok_aff, msg_aff = self.apply_game_affinity_all_cores(profile.game_label)
            overall_ok = overall_ok and ok_aff
            lines.append(f"[Affinity] {msg_aff}")
        else:
            # "custom" or unknown – not implemented yet
            lines.append("[Affinity] Custom affinity not implemented yet; skipped.")

        # (Future) per-game Nagle toggles could hook in here.

        # Summary
        header = "[Profile] Applied"
        if has_file:
            header += " (from saved profile file)."
        else:
            header += " (using built-in defaults)."
        lines.insert(1, header)

        return overall_ok, "\n".join(lines)
