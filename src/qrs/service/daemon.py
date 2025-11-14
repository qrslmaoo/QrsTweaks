# src/qrs/service/daemon.py

from __future__ import annotations

import time, json
from pathlib import Path

from src.qrs.modules.game_optim import GameOptimizer
from src.qrs.modules.telemetry_live import TelemetryLive

LOG_DIR = Path("Logs")
LOG_FILE = LOG_DIR / "daemon.log"
LOG_DIR.mkdir(exist_ok=True, parents=True)
STOP_FLAG = LOG_DIR / "daemon.stop"

SLEEP_INTERVAL = 1.0


def _log(evt: str, data=None):
    entry = {
        "ts": time.time(),
        "event": evt,
        "info": data or {},
    }
    txt = json.dumps(entry)
    if LOG_FILE.exists():
        LOG_FILE.write_text(LOG_FILE.read_text() + txt + "\n")
    else:
        LOG_FILE.write_text(txt + "\n")


def run_daemon() -> int:
    opt = GameOptimizer()
    tel = TelemetryLive()
    current = None  # (game_label, pid)

    _log("daemon_started")

    try:
        while True:
            # ---- Game detection (Phase 6 logic) ----
            for label in ("Fortnite", "Minecraft", "Valorant", "Call of Duty"):
                ok, msg, proc = opt.find_game_process(label, timeout_sec=0)
                if ok:
                    pid = proc.pid

                    if current is None or current[0] != label:
                        current = (label, pid)
                        _log("game_started", {"game": label, "pid": pid})

                        opt.apply_game_priority(label, "HIGH")
                        if label.startswith("Fortnite"):
                            opt.apply_fortnite_gaming_preset()
                        opt.apply_game_affinity_recommended(label)

                        _log("optimizations_applied", {"game": label})
                else:
                    if current and current[0] == label:
                        _log("game_stopped", {"game": label})
                        current = None

            # ---- NEW: system telemetry ----
            snap = tel.sample()
            tel.write_snapshot(snap)

            time.sleep(SLEEP_INTERVAL)

    except Exception as e:
        _log("daemon_error", {"error": repr(e)})
        return 1

    return 0
