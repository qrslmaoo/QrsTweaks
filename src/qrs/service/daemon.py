# src/qrs/service/daemon.py

from __future__ import annotations

"""
QrsTweaks Background Daemon (Pure Python)

Purpose:
    - Runs as a lightweight background loop
    - Detects running games (Fortnite, Minecraft, Valorant, Call of Duty)
    - Auto-applies safe gaming presets when a game is detected
    - Optionally applies CPU priority / affinity (via GameOptimizer)
    - Logs everything to logs/qrs_daemon.log

Usage (from project root):
    python -m src.qrs.service.daemon

Architecture:
    - No Windows Service, no installer magic
    - Just a normal background process you can start/stop
    - Designed to be wired into the UI later (Phase 10B/10C)
"""

import sys
import time
import platform
from pathlib import Path
from typing import Dict, Optional

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional
    psutil = None

# Local imports – these already exist in your project
from src.qrs.modules.windows_optim import WindowsOptimizer
from src.qrs.modules.game_optim import GameOptimizer, ProcessInfo


def _is_windows() -> bool:
    return platform.system() == "Windows"


class QrsDaemon:
    """
    Core background loop.

    Responsibilities:
        - Monitor for running games (Fortnite, Minecraft, Valorant, CoD)
        - When a game (Fortnite) is detected for the first time in this session:
            * Apply Fortnite gaming preset (cache clean + DVR/GameBar disable)
        - (Future) Use GameOptimizer.apply_game_priority / affinity helpers
        - Periodically log system snapshot (CPU / RAM)
    """

    def __init__(
        self,
        poll_interval_sec: float = 5.0,
        system_snapshot_every_n_loops: int = 12,  # ~1 snapshot/min at 5s interval
    ) -> None:
        self.poll_interval_sec = max(1.0, float(poll_interval_sec))
        self.system_snapshot_every_n_loops = max(1, int(system_snapshot_every_n_loops))

        self.root = Path.cwd()
        self.logs_dir = self.root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / "qrs_daemon.log"

        self.win_opt = WindowsOptimizer()
        self.game_opt = GameOptimizer()

        # Track which game labels we’ve already applied presets for in this session
        self._seen_games: Dict[str, int] = {}  # label -> pid
        self._loop_counter: int = 0
        self._running: bool = False

    # -------------------------------------------------
    # Logging helper
    # -------------------------------------------------
    def _log(self, message: str) -> None:
        """
        Append a timestamped line to qrs_daemon.log and stdout.
        """
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{ts}] {message}"
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            # Logging failure should never kill the daemon
            pass
        print(line, flush=True)

    # -------------------------------------------------
    # Game handling
    # -------------------------------------------------
    def _tracked_game_labels(self) -> list[str]:
        """
        Games we care about in the daemon.
        Labels must match the combo text or be understandable
        by GameOptimizer._game_to_process_names().
        """
        return [
            "Fortnite",
            "Minecraft",
            "Valorant",
            "Call of Duty",
        ]

    def _get_game_pid(self, label: str) -> Optional[int]:
        """
        Lightweight, single-shot PID lookup.
        """
        try:
            pid = self.game_opt.get_game_pid_or_none(label)
            return pid
        except Exception as e:
            self._log(f"[Daemon/Game] Error while checking PID for '{label}': {e!r}")
            return None

    def _handle_game_detection(self) -> None:
        """
        Scan for running games and trigger presets when we see a new one.
        """
        for label in self._tracked_game_labels():
            pid = self._get_game_pid(label)
            if pid is None:
                # Game not running
                if label in self._seen_games:
                    # It was running before, now it's gone
                    self._log(f"[Game] {label} exited (PID {self._seen_games[label]}).")
                    del self._seen_games[label]
                continue

            prev_pid = self._seen_games.get(label)
            if prev_pid == pid:
                # Already seen this instance
                continue

            # New instance detected
            self._seen_games[label] = pid
            self._log(f"[Game] Detected '{label}' running with PID {pid}.")

            # Per-game behavior
            if label == "Fortnite":
                self._apply_fortnite_autotune(pid)
            else:
                # Future: build per-game presets
                self._log(f"[Game] No dedicated preset yet for '{label}'. Skipping auto-tweaks.")

    def _apply_fortnite_autotune(self, pid: int) -> None:
        """
        Called when we detect a new Fortnite instance.
        """
        self._log(f"[Fortnite] Applying Fortnite gaming preset for PID {pid}.")

        # Step 1: Fortnite preset (cache clean + GameBar/GameDVR off)
        try:
            ok_preset, msg_preset = self.game_opt.apply_fortnite_gaming_preset()
            level = "OK" if ok_preset else "WARN"
            for line in msg_preset.splitlines():
                self._log(f"[Fortnite/{level}] {line}")
        except Exception as e:
            self._log(f"[Fortnite/ERROR] Failed to apply gaming preset: {e!r}")

        # Step 2: Try to set process priority (best-effort)
        try:
            ok_prio, msg_prio = self.game_opt.apply_game_priority("Fortnite", "HIGH")
            level = "OK" if ok_prio else "WARN"
            self._log(f"[Fortnite/{level}] {msg_prio}")
        except Exception as e:
            self._log(f"[Fortnite/ERROR] Failed to set process priority: {e!r}")

        # Step 3: Try to bind to recommended gaming cores
        try:
            ok_aff, msg_aff = self.game_opt.apply_game_affinity_recommended("Fortnite")
            level = "OK" if ok_aff else "WARN"
            self._log(f"[Fortnite/{level}] {msg_aff}")
        except Exception as e:
            self._log(f"[Fortnite/ERROR] Failed to set CPU affinity: {e!r}")

    # -------------------------------------------------
    # System snapshot (CPU / RAM)
    # -------------------------------------------------
    def _log_system_snapshot(self) -> None:
        """
        Periodically log overall CPU / RAM usage.
        Uses psutil if available; falls back gracefully if not.
        """
        if psutil is None:
            self._log("[System] psutil not installed; skipping snapshot.")
            return

        try:
            cpu = psutil.cpu_percent(interval=0.1)  # type: ignore[attr-defined]
            mem = psutil.virtual_memory()  # type: ignore[attr-defined]
            self._log(
                f"[System] CPU={cpu:.1f}% "
                f"RAM={mem.percent:.1f}% "
                f"({mem.used / (1024**3):.2f}GB / {mem.total / (1024**3):.2f}GB)"
            )
        except Exception as e:
            self._log(f"[System] Failed to collect snapshot: {e!r}")

    # -------------------------------------------------
    # Main loop
    # -------------------------------------------------
    def run_forever(self) -> None:
        """
        Blocking main loop. Use Ctrl+C to stop.
        """
        if not _is_windows():
            self._log("[Daemon] Not running on Windows. Exiting.")
            return

        self._running = True
        self._log(
            "[Daemon] QrsTweaks background daemon started "
            f"(interval={self.poll_interval_sec:.1f}s)."
        )

        try:
            while self._running:
                self._loop_counter += 1

                # 1) Game detection / auto-tweaks
                self._handle_game_detection()

                # 2) Periodic system snapshot
                if self._loop_counter % self.system_snapshot_every_n_loops == 0:
                    self._log_system_snapshot()

                time.sleep(self.poll_interval_sec)
        except KeyboardInterrupt:
            self._log("[Daemon] KeyboardInterrupt received; shutting down.")
        except Exception as e:
            self._log(f"[Daemon] Unhandled exception: {e!r}")
        finally:
            self._running = False
            self._log("[Daemon] Stopped.")

    def stop(self) -> None:
        """
        Signal the loop to stop on the next iteration.
        """
        self._running = False


# -----------------------------------------------------
# CLI entry point
# -----------------------------------------------------
def main() -> None:
    """
    CLI entry. Makes this runnable via:

        python -m src.qrs.service.daemon
    """
    daemon = QrsDaemon()
    daemon.run_forever()


if __name__ == "__main__":
    main()
