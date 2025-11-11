# src/qrs/modules/fps_monitor.py
import subprocess
import threading
import time
import shutil
import re
from pathlib import Path
from collections import deque


class FortniteFPSMonitor:
    """
    Fortnite FPS monitor with two backends:
      1) PresentMon (preferred) if tools/PresentMon.exe exists
      2) Fallback: polling no-FPS (reports 'N/A'), keeps UI stable

    How to enable best results:
      - Put PresentMon.exe into: tools/PresentMon/PresentMon.exe  (or tools/PresentMon.exe)
      - We launch with: --process_name FortniteClient-Win64-Shipping.exe --no_summary --output_stdout
    """

    def __init__(self):
        self.proc = None
        self.thread = None
        self.stop_flag = threading.Event()
        self.fps_history = deque(maxlen=240)  # ~4s @60hz
        self.presentmon_path = self._find_presentmon()

    def _find_presentmon(self):
        # Try a few common spots inside repo
        root = Path(__file__).resolve().parents[3]
        candidates = [
            root / "tools" / "PresentMon.exe",
            root / "tools" / "PresentMon" / "PresentMon.exe",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        # Try PATH
        if shutil.which("PresentMon.exe"):
            return shutil.which("PresentMon.exe")
        return None

    def start(self):
        """Start monitoring; returns True if PresentMon backend used."""
        self.stop()
        self.stop_flag.clear()

        if self.presentmon_path:
            cmd = [
                self.presentmon_path,
                "--process_name", "FortniteClient-Win64-Shipping.exe",
                "--no_csv",
                "--no_summary",
                "--output_stdout",
            ]
            # Spawn reader thread
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            self.thread = threading.Thread(target=self._reader_presentmon, daemon=True)
            self.thread.start()
            return True
        else:
            # Fallback thread (keeps UI alive, reports N/A)
            self.thread = threading.Thread(target=self._reader_fallback, daemon=True)
            self.thread.start()
            return False

    def stop(self):
        self.stop_flag.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None

    def _reader_presentmon(self):
        fps_re = re.compile(r"^\s*[-\d:.]+\s+([-]?\d+(?:\.\d+)?)\s*$")  # loose fallback
        # PresentMon prints rows; we'll scan for "msBetweenPresents" or "FPS" lines across versions
        for line in self.proc.stdout:
            if self.stop_flag.is_set():
                break
            # Many builds output CSV-ish or tabbed lines. Try to catch a numeric FPS in the line.
            # Prefer "AverageFPS=" style first:
            m = re.search(r"FPS[:=]\s*([0-9]+(?:\.[0-9]+)?)", line)
            if not m:
                # Some builds output "MsBetweenPresents=xx"; fps=1000/mbp
                mbp = re.search(r"MsBetweenPresents[:=]\s*([0-9]+(?:\.[0-9]+)?)", line, re.I)
                if mbp:
                    try:
                        fps = 1000.0 / float(mbp.group(1))
                        self.fps_history.append(fps)
                    except Exception:
                        pass
                    continue
                # Try generic last-number grab
                m = fps_re.match(line.strip())
            if m:
                try:
                    fps = float(m.group(1))
                    self.fps_history.append(fps)
                except Exception:
                    pass
        # graceful exit
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

    def _reader_fallback(self):
        # Report 'N/A' by pushing -1 sentinel every second
        while not self.stop_flag.is_set():
            self.fps_history.append(-1.0)
            time.sleep(1.0)

    def latest_fps(self):
        """Return (fps, backend) where fps may be -1.0 for N/A"""
        backend = "PresentMon" if self.presentmon_path else "None"
        if not self.fps_history:
            return -1.0, backend
        return self.fps_history[-1], backend
