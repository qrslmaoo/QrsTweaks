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
- Generic per-game storage helpers (Phase 4C)
"""

import os
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Tuple, Dict, NamedTuple, List

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional
    psutil = None


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
            clean_game_temp(...)
            clean_game_crashes(...)
            clean_game_shaders(...)
            reset_game_config(...)
            disable_nagle_for_game(...)
    """

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
            config    -> Saved/Config/WindowsClient
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
                "config": dummy / "Config" / "WindowsClient",
            }

        base = Path(lad) / "FortniteGame" / "Saved"
        return {
            "base": base,
            "logs": base / "Logs",
            "crashes": base / "Crashes",
            "shaders": base / "ShaderCaches",
            "config": base / "Config" / "WindowsClient",
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
    #   GENERIC GAME STORAGE HELPERS (Phase 4C)
    # =========================================================

    def _game_root_path(self, game_label: str) -> Path | None:
        """
        Best-effort guess at a per-game 'root' folder for temp / config.

        This is intentionally conservative and only touches user-space
        locations under %LOCALAPPDATA% / %APPDATA%.
        """
        label = (game_label or "").strip().lower()
        lad = os.environ.get("LOCALAPPDATA") or ""
        rad = os.environ.get("APPDATA") or ""

        if not lad and not rad:
            return None

        lad_p = Path(lad) if lad else None
        rad_p = Path(rad) if rad else None

        if label.startswith("fortnite"):
            paths = self._fortnite_paths()
            return paths["base"]

        if label.startswith("minecraft"):
            # Classic Java path
            if rad_p is not None:
                return rad_p / ".minecraft"
            return None

        # For now, other games are not guessed; we keep it safe.
        return None

    def clean_game_temp(self, game_label: str) -> Tuple[bool, str]:
        """
        Clean per-game temp-like folders where it is safe to do so.
        Currently implemented for:
          - Fortnite (Saved/Temp if present)
          - Minecraft (.minecraft/temp, if present)
        """
        root = self._game_root_path(game_label)
        if root is None:
            return False, f"No known safe temp path for '{game_label}'."

        candidates: List[Path] = []
        label = (game_label or "").strip().lower()

        if label.startswith("fortnite"):
            paths = self._fortnite_paths()
            candidates.append(paths["base"] / "Temp")
        elif label.startswith("minecraft"):
            candidates.append(root / "temp")

        total = 0
        for c in candidates:
            total += self._delete_dir_contents(c)

        if total == 0:
            return False, f"No temp files removed for '{game_label}' (folders missing or empty)."
        return True, f"Removed ~{total} temp entries for '{game_label}'."

    def clean_game_crashes(self, game_label: str) -> Tuple[bool, str]:
        """
        Clean per-game crash dumps / logs where we know locations.
        """
        label = (game_label or "").strip().lower()

        if label.startswith("fortnite"):
            return self.clean_fortnite_logs_and_crashes()

        # Minecraft, Valorant, CoD, etc. can be added later.
        return False, f"Crash cleanup not implemented yet for '{game_label}'."

    def clean_game_shaders(self, game_label: str) -> Tuple[bool, str]:
        """
        Clean per-game shader / pipeline caches where it is safe.
        """
        label = (game_label or "").strip().lower()

        if label.startswith("fortnite"):
            return self.clean_fortnite_shader_cache()

        # For other engines we hold off until paths are fully mapped.
        return False, f"Shader cache cleanup not implemented yet for '{game_label}'."

    def reset_game_config(self, game_label: str) -> Tuple[bool, str]:
        """
        Reset per-game config by backing up and deleting known config files.

        Currently implemented for:
          - Fortnite: Saved/Config/WindowsClient/*.ini
        """
        label = (game_label or "").strip().lower()
        if not label.startswith("fortnite"):
            return False, f"Config reset not implemented yet for '{game_label}'."

        paths = self._fortnite_paths()
        cfg_dir = paths["config"]
        if not cfg_dir.exists() or not cfg_dir.is_dir():
            return False, f"Config directory not found for Fortnite: {cfg_dir}"

        backup_dir = cfg_dir.parent / "WindowsClient.backup"
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Failed to create backup folder: {e!r}"

        moved = 0
        for child in cfg_dir.iterdir():
            if not child.is_file():
                continue
            try:
                target = backup_dir / child.name
                if target.exists():
                    target.unlink()
                child.rename(target)
                moved += 1
            except Exception:
                continue

        if moved == 0:
            return False, f"No config files moved for Fortnite (folder may already be empty): {cfg_dir}"
        return True, f"Backed up and cleared {moved} config files from {cfg_dir}."

    # =========================================================
    #   NAGLE / LATENCY PRESET (Phase 4D)
    # =========================================================

    def disable_nagle_for_game(self, game_label: str) -> Tuple[bool, str]:
        """
        For now, this is a thin wrapper that simply logs intent.

        A full per-game Nagle implementation would require mapping
        game sockets to specific interfaces / ports, which is outside
        the current scope. Instead we:
          - Rely on the global Windows optimizer for registry-based Nagle
          - Log that this preset was requested for visibility
        """
        label = (game_label or "").strip() or "<unknown>"
        # This is intentionally a no-op in terms of system changes.
        return True, (
            f"Nagle low-latency preset requested for '{label}'. "
            "Apply global Nagle toggles from the Windows optimizer page for full effect."
        )
