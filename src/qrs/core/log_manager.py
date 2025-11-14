# src/qrs/core/log_manager.py

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any


class LogManager:
    """
    Global logging core for QrsTweaks.

    Features:
      - Thread-safe JSONL logging to /logs/YYYY-MM-DD.jsonl
      - In-memory subscribers for live UI (Timeline page)
      - Optional global status handler (wired from SuiteWindow)

    Typical usage:

        from src.qrs.core.log_manager import log_mgr

        log_mgr.log("Windows", "Deep cleanup removed 120 items", level="ok")
        log_mgr.log("Game", "Fortnite preset applied", level="ok", bubble=True)
    """

    def __init__(self) -> None:
        # Resolve project root: src/qrs/core/log_manager.py -> <root>
        here = Path(__file__).resolve()
        # parents: 0=core, 1=qrs, 2=src, 3=root
        self.root = here.parents[3]
        self.logs_dir = self.root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self._status_handler: Optional[Callable[[str, str], None]] = None  # (level, msg)

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def set_status_handler(self, handler: Callable[[str, str], None]) -> None:
        """
        Set a callback for 'bubble' status notifications.

        handler(level, message)
        """
        self._status_handler = handler

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to live log entries.

        callback(entry: dict) where entry has keys:
            ts, source, level, message, extra
        """
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def log(
        self,
        source: str,
        message: str,
        level: str = "info",
        *,
        extra: Optional[Dict[str, Any]] = None,
        bubble: bool = False,
    ) -> None:
        """
        Append a log entry to the current day's JSONL file and notify subscribers.

        Args:
            source: "Windows", "Game", "Dashboard", "Timeline", etc.
            message: Human-readable message
            level: "info", "ok", "warn", "error"
            extra: Optional dict of extra data (must be JSON-serializable)
            bubble: If True, forwards message to status handler (SuiteWindow)
        """
        entry = {
            "ts": time.time(),
            "source": str(source),
            "level": str(level).lower(),
            "message": str(message),
            "extra": extra or {},
        }

        # Normalize level a bit
        if entry["level"] not in {"info", "ok", "warn", "error"}:
            entry["level"] = "info"

        line = json.dumps(entry, ensure_ascii=False)

        with self._lock:
            try:
                path = self._current_log_file()
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                # Logging must never crash the app; swallow file errors.
                pass

            # Notify subscribers (Timeline, etc.)
            dead: List[Callable[[Dict[str, Any]], None]] = []
            for cb in self._subscribers:
                try:
                    cb(entry)
                except Exception:
                    dead.append(cb)
            for cb in dead:
                if cb in self._subscribers:
                    self._subscribers.remove(cb)

        # Optional bubble to status bar
        if bubble and self._status_handler is not None:
            try:
                self._status_handler(entry["level"], f"{entry['source']}: {entry['message']}")
            except Exception:
                pass

    def get_recent_entries(self, max_entries: int = 300) -> List[Dict[str, Any]]:
        """
        Read the current day's log file and return the last max_entries entries.
        """
        path = self._current_log_file()
        if not path.exists():
            return []

        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return []

        entries: List[Dict[str, Any]] = []
        for line in lines[-max_entries:]:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    entries.append(data)
            except json.JSONDecodeError:
                continue
        return entries

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------
    def _current_log_file(self) -> Path:
        date_str = time.strftime("%Y-%m-%d")
        return self.logs_dir / f"{date_str}.jsonl"


# Global singleton used across the app
log_mgr = LogManager()
