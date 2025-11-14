# src/qrs/service/daemon_main.py
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path


def _runtime_dir() -> Path:
    """
    Resolve the project root and ensure a .runtime folder exists.

    This assumes the repo layout:
        QrsTweaks/
          src/
            qrs/
              service/
                daemon_main.py
    """
    here = Path(__file__).resolve()
    # .../QrsTweaks/src/qrs/service/daemon_main.py
    # parents[0] = service, [1] = qrs, [2] = src, [3] = QrsTweaks
    root = here.parents[3]
    runtime = root / ".runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


def _state_path() -> Path:
    return _runtime_dir() / "daemon_state.json"


def main() -> None:
    """
    Minimal daemon loop:

      - Writes pid + last_heartbeat into daemon_state.json
      - Sleeps 5 seconds
      - Repeats until killed

    Any future auto-optimization logic can hook in here, keeping the
    interface to the UI stable.
    """
    state_file = _state_path()

    while True:
        now = datetime.utcnow().isoformat() + "Z"
        state = {
            "pid": os.getpid(),
            "status": "running",
            "last_heartbeat": now,
        }
        try:
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            # Best-effort only, never crash the daemon on I/O errors
            pass

        time.sleep(5.0)


if __name__ == "__main__":
    main()
