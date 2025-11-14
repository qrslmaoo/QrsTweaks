# src/qrs/service/daemon_main.py

from __future__ import annotations
import sys
from src.qrs.service.daemon import run_daemon

if __name__ == "__main__":
    sys.exit(run_daemon())
