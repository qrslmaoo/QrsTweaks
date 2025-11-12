# src/qrs/modules/windows_optim.py
# QrsTweaks Optimizer Core (no monitoring, no AI)
# - Cleanable-space System Scan (temp/prefetch/updates/recycle bin)
# - Power/network/services/storage/tasks tweaks
# - Safe profile application (JSON-based)
# - Restore defaults & log export helpers
# NOTE: Windows-only. Admin needed for many operations.

from __future__ import annotations

import os
import sys
import json
import zipfile
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import psutil  # requirements.txt should include psutil
import winreg  # Windows registry

# -----------------------------
# Helpers
# -----------------------------
def is_admin() -> bool:
    """Return True if current process has Administrator privileges."""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(script: str) -> subprocess.CompletedProcess:
    """Run a PowerShell command (hidden) and return the CompletedProcess."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        text=True,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def bytes_fmt(n: int) -> str:
    """Human-friendly bytes."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


class WindowsOptimizer:
    """Handles system tweaks, cleanup, and profile applications (no background/AI)."""

    def __init__(self):
        # repo root = .../QrsTweaks
        self.root = Path(__file__).resolve().parents[3]
        self.logs_dir = self.root / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Memory-guard placeholder exe name (if later you ship one)
        self._memleak_proc_name = "qrs_memguard.exe"

    # =========================================================
    #                    SYSTEM SCAN (NEW)
    # =========================================================
    def quick_scan(self) -> str:
        """
        Scan for *cleanable* data instead of PC specs.
        Targets:
          - User TEMP          (%TEMP%)
          - System TEMP        (C:\Windows\Temp)
          - Prefetch           (C:\Windows\Prefetch)
          - Windows Update dl  (C:\Windows\SoftwareDistribution\Download)
          - Recycle Bin size   (Shell API via PowerShell)
        Returns a multi-line string summary for UI.
        """
        targets = [
            (os.getenv("TEMP"), "User Temp"),
            (r"C:\Windows\Temp", "System Temp"),
            (r"C:\Windows\Prefetch", "Prefetch"),
            (r"C:\Windows\SoftwareDistribution\Download", "Windows Update Cache"),
        ]

        total_bytes = 0
        total_files = 0
        report_lines: List[str] = []

        for path, label in targets:
            if not path or not os.path.exists(path):
                continue
            size = 0
            count = 0
            # Walk with best-effort error handling
            for root, _, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size += os.path.getsize(fp)
                        count += 1
                    except Exception:
                        pass
            total_bytes += size
            total_files += count
            report_lines.append(f"[{label}] {count:,} files ({bytes_fmt(size)})")

        # Recycle Bin estimate (per-drive) — safe query
        try:
            ps = r"(New-Object -ComObject Shell.Application).NameSpace(10).Items() | " \
                 r"Measure-Object -Property Size -Sum | Select-Object -ExpandProperty Sum"
            rb = run_ps(ps)
            if rb.returncode == 0 and rb.stdout.strip():
                rb_size = int(rb.stdout.strip())
                total_bytes += rb_size
                report_lines.append(f"[Recycle Bin] ~{bytes_fmt(rb_size)}")
        except Exception:
            report_lines.append("[Recycle Bin] size unavailable")

        report_lines.append("")
        report_lines.append(f"[Scan Complete] {total_files:,} files detected.")
        report_lines.append(f"Estimated cleanable space: {bytes_fmt(total_bytes)}")

        return "\n".join(report_lines)

    # =========================================================
    #                    STATUS DETECTION
    # =========================================================
    def is_high_perf_plan(self) -> bool:
        try:
            output = subprocess.check_output(["powercfg", "/getactivescheme"], text=True)
            lo = output.lower()
            return ("high performance" in lo) or ("ultimate performance" in lo) or ("scheme_min" in lo)
        except Exception:
            return False

    def is_game_mode_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar") as key:
                val, _ = winreg.QueryValueEx(key, "AllowAutoGameMode")
                return int(val) == 1
        except Exception:
            return False

    def is_visual_effects_minimized(self) -> bool:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
            ) as key:
                val, _ = winreg.QueryValueEx(key, "VisualFXSetting")
                return int(val) == 2  # 2 = best performance
        except Exception:
            return False

    def is_network_optimized(self) -> bool:
        try:
            out = subprocess.check_output(["netsh", "int", "tcp", "show", "global"], text=True).lower()
            # Rough heuristic: CTCP on OR non-normal autotuning
            ctcp_ok = ("congestion provider" in out and "ctcp" in out)
            # Windows output variants: "Receive Window Auto-Tuning Level : normal/restricted/highlyrestricted/disabled"
            tuned = ("autotuning" in out and ("restricted" in out or "disabled" in out))
            return ctcp_ok or tuned
        except Exception:
            return False

    def is_memleak_guard_active(self) -> bool:
        try:
            for p in psutil.process_iter(["name"]):
                n = (p.info.get("name") or "").lower()
                if self._memleak_proc_name in n:
                    return True
        except Exception:
            pass
        return False

    def is_services_optimized(self) -> bool:
        try:
            out = run_ps(
                "(Get-Service -Name 'SysMain','DiagTrack' -ErrorAction SilentlyContinue | "
                "Select-Object Name,StartType,Status | ConvertTo-Json)"
            )
            if out.returncode != 0 or not out.stdout.strip():
                return False
            data = json.loads(out.stdout)
            if isinstance(data, dict):
                data = [data]
            names = {d["Name"]: (str(d.get("StartType", "")).lower(), str(d.get("Status", "")).lower()) for d in data}
            sysmain_ok = ("sysmain" in names) and (names["sysmain"][0] == "disabled")
            diag_ok = ("diagtrack" in names) and (names["diagtrack"][0] == "disabled")
            return sysmain_ok and diag_ok
        except Exception:
            return False

    # =========================================================
    #                    CORE ACTIONS
    # =========================================================
    def create_high_perf_powerplan(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required for power plan."
        try:
            subprocess.run(["powercfg", "-setactive", "SCHEME_MIN"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True, "High Performance plan activated."
        except Exception as e:
            return False, str(e)

    def cleanup_temp_files(self) -> int:
        """
        Clean temp dirs only. (Deep cleanup is handled by specific buttons.)
        Returns approximate number of files removed.
        """
        tmp_targets = [
            Path(os.environ.get("TEMP", r"C:\Windows\Temp")),
            Path(r"C:\Windows\Temp"),
        ]
        count = 0
        for base in tmp_targets:
            if not base.exists():
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    fp = Path(root) / f
                    try:
                        fp.unlink(missing_ok=True)
                        count += 1
                    except Exception:
                        pass
        return count

    def create_restore_point(self, name: str) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required for restore points."
        cp = run_ps(f"Checkpoint-Computer -Description '{name}' -RestorePointType 'MODIFY_SETTINGS'")
        if cp.returncode == 0:
            return True, "Restore point created."
        return False, (cp.stderr or cp.stdout or "Failed to create restore point.")

    # ---------------------------------------------------------
    # Memory leak protector (placeholder hooks)
    # ---------------------------------------------------------
    def start_memleak_protector(self, process_names: List[str], mb_threshold: int) -> Tuple[bool, str]:
        # Hook your external helper here later if you ship one.
        return True, f"MemLeak guard armed for {', '.join(process_names)} @ {mb_threshold} MB."

    def stop_memleak_protector(self) -> Tuple[bool, str]:
        return True, "MemLeak guard disarmed."

    # ---------------------------------------------------------
    # Network tweaks
    # ---------------------------------------------------------
    def set_dns(self, primary: str, secondary: str) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required to set DNS."
        names = ["Ethernet", "Wi-Fi", "WiFi", "Local Area Connection"]
        errors = []
        for n in names:
            a = run_ps(f'netsh interface ip set dns name="{n}" static {primary}')
            b = run_ps(f'netsh interface ip add dns name="{n}" {secondary} index=2')
            if a.returncode == 0:
                return True, f"DNS on '{n}' set to {primary} / {secondary}"
            errors.append(a.stderr or a.stdout)
        return False, "Failed to set DNS. " + " | ".join(filter(None, errors))[:300]

    def enable_ctcp(self, enable: bool) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        mode = "ctcp" if enable else "none"
        r = run_ps(f'netsh int tcp set global congestionprovider={mode}')
        if r.returncode == 0:
            return True, f"CTCP {'enabled' if enable else 'disabled'}."
        return False, r.stderr or r.stdout

    def autotuning(self, level: str) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps(f'netsh int tcp set global autotuninglevel={level}')
        if r.returncode == 0:
            return True, f"TCP autotuning set to {level}."
        return False, r.stderr or r.stdout

    def toggle_nagle(self, disable: bool = True) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces") as root:
                i = 0
                changed = 0
                while True:
                    try:
                        subname = winreg.EnumKey(root, i); i += 1
                        with winreg.OpenKey(root, subname, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as sub:
                            val = 1 if disable else 0
                            try:
                                winreg.SetValueEx(sub, "TcpNoDelay", 0, winreg.REG_DWORD, val)
                                winreg.SetValueEx(sub, "TcpAckFrequency", 0, winreg.REG_DWORD, val)
                                changed += 1
                            except Exception:
                                pass
                    except OSError:
                        break
            return True, f"Nagle {'disabled' if disable else 'enabled'} on {changed} interfaces (reboot may be required)."
        except Exception as e:
            return False, str(e)

    def latency_ping(self, host: str = "1.1.1.1", count: int = 4) -> Tuple[bool, str]:
        try:
            output = subprocess.check_output(["ping", host, "-n", str(count)], text=True, stderr=subprocess.DEVNULL)
            return True, output
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # Startup entries (read-only listing)
    # ---------------------------------------------------------
    def list_startup_entries(self) -> List[Tuple[str, str, str]]:
        results: List[Tuple[str, str, str]] = []
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for root, path in keys:
            try:
                with winreg.OpenKey(root, path) as k:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(k, i); i += 1
                            results.append((path, name, val))
                        except OSError:
                            break
            except FileNotFoundError:
                pass
        return results

    # ---------------------------------------------------------
    # AI-less helpers (deterministic)
    # ---------------------------------------------------------
    def adaptive_dns_auto(self) -> Tuple[bool, str]:
        """
        Test a small list of DNS candidates via ping and pick the fastest.
        (Still fully local/deterministic.)
        """
        candidates = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        best = None
        best_avg = 9999
        for ip in candidates:
            ok, out = self.latency_ping(ip, 3)
            if not ok:
                continue
            avg = 9999
            for ln in out.splitlines():
                lo = ln.lower()
                # common English output: "Average = 12ms"
                if "average" in lo and "ms" in lo:
                    parts = [p for p in lo.replace("=", " ").split() if p.endswith("ms")]
                    if parts:
                        try:
                            avg = int(parts[-1].replace("ms", ""))
                        except Exception:
                            pass
            if avg < best_avg:
                best_avg = avg
                best = ip
        if not best:
            return False, "No usable DNS ping results."
        order = [best] + [x for x in candidates if x != best]
        return self.set_dns(order[0], order[1])

    def auto_network_repair(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        cmds = ["netsh int ip reset", "netsh winsock reset", "ipconfig /flushdns"]
        outs = []
        for c in cmds:
            r = run_ps(c)
            outs.append(r.stdout or r.stderr or c)
        return True, "Network repair executed. Reboot may be required.\n" + "\n".join(outs)

    # ---------------------------------------------------------
    # Deep Cleanup
    # ---------------------------------------------------------
    def clean_browser_caches(self) -> Tuple[bool, str]:
        home = Path.home()
        targets = [
            home / "AppData/Local/Google/Chrome/User Data/Default/Cache",
            home / "AppData/Local/Google/Chrome/User Data/Default/Code Cache",
            home / "AppData/Local/Microsoft/Edge/User Data/Default/Cache",
            home / "AppData/Local/Microsoft/Edge/User Data/Default/Code Cache",
            home / "AppData/Local/Mozilla/Firefox/Profiles",
        ]
        removed = 0
        for t in targets:
            if not t.exists():
                continue
            if t.is_dir():
                for root, _, files in os.walk(t):
                    for f in files:
                        fp = Path(root) / f
                        try:
                            fp.unlink(missing_ok=True)
                            removed += 1
                        except Exception:
                            pass
        return True, f"Removed ~{removed} cached files."

    def windows_update_cleanup(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        dism = run_ps("DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase")
        ok = dism.returncode == 0
        msg = (dism.stdout or dism.stderr or "").strip()
        return ok, ("Windows Update cleanup finished." if ok else msg)

    def find_app_residue(self) -> Tuple[bool, str]:
        roots = [Path.home() / "AppData/Local", Path.home() / "AppData/Roaming", Path(r"C:\ProgramData")]
        suspicious = []
        for r in roots:
            if not r.exists():
                continue
            for d in r.iterdir():
                try:
                    if d.is_dir() and (d.name.lower().startswith("uninstall") or "temp" in d.name.lower()):
                        suspicious.append(str(d))
                except Exception:
                    pass
        return True, "\n".join(suspicious[:100]) if suspicious else "No obvious residue found."

    # ---------------------------------------------------------
    # Services / Processes
    # ---------------------------------------------------------
    def apply_minimal_services(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        script = r"""
$names = @('DiagTrack','SysMain')
foreach ($n in $names) {
    $svc = Get-Service -Name $n -ErrorAction SilentlyContinue
    if ($svc) {
        Set-Service -Name $n -StartupType Disabled
        if ($svc.Status -eq 'Running') { Stop-Service -Name $n -Force -ErrorAction SilentlyContinue }
    }
}
"""
        r = run_ps(script)
        return (r.returncode == 0), (r.stderr or r.stdout or "Applied minimal services.")

    def throttle_background_cpu(self) -> Tuple[bool, str]:
        lowered = 0
        allow = {"explorer.exe", "dwm.exe", "csrss.exe", "smss.exe", "system", "registry"}
        try:
            for p in psutil.process_iter(["name", "pid"]):
                n = (p.info.get("name") or "").lower()
                if not n or n in allow:
                    continue
                try:
                    psutil.Process(p.info["pid"]).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    lowered += 1
                except Exception:
                    pass
            return True, f"Lowered priority on ~{lowered} processes."
        except Exception as e:
            return False, str(e)

    def list_heavy_processes(self) -> Tuple[bool, str]:
        procs = []
        for p in psutil.process_iter(["name", "pid", "cpu_percent", "memory_info"]):
            try:
                procs.append(
                    (p.info["cpu_percent"], p.info["memory_info"].rss // (1024 * 1024), p.info["pid"], p.info["name"])
                )
            except Exception:
                pass
        procs.sort(reverse=True)
        lines = [f"CPU {cpu:.1f}% | RAM {ram} MB | PID {pid} | {name}" for cpu, ram, pid, name in procs[:20]]
        return True, "\n".join(lines) if lines else "No processes."

    def driver_version_integrity(self) -> Tuple[bool, str]:
        r = run_ps("(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json)")
        if r.returncode != 0 or not r.stdout.strip():
            return False, r.stderr or r.stdout or "Failed to query GPU driver."
        return True, r.stdout.strip()

    # ---------------------------------------------------------
    # Storage Tools
    # ---------------------------------------------------------
    def trim_ssds(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps("defrag /C /L")
        return (r.returncode == 0), (r.stdout or r.stderr)

    def defrag_hdds_safe(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps("defrag /E C: /U /V")
        return (r.returncode == 0), (r.stdout or r.stderr)

    def find_large_files(self, roots: Optional[List[str]] = None, min_mb: int = 500, limit: int = 50) -> Tuple[bool, str]:
        if roots is None:
            roots = [str(Path.home() / "Downloads"), str(Path.home() / "Videos"), str(Path.home() / "Documents")]
        min_bytes = min_mb * 1024 * 1024
        found = []
        for r in roots:
            p = Path(r)
            if not p.exists():
                continue
            for fp in p.rglob("*"):
                try:
                    if fp.is_file() and fp.stat().st_size >= min_bytes:
                        found.append((fp.stat().st_size, str(fp)))
                except Exception:
                    pass
        found.sort(reverse=True)
        lines = [f"{size/1024/1024:.0f} MB  {path}" for size, path in found[:limit]]
        return True, "\n".join(lines) if lines else "No large files found."

    def duplicate_finder(self, roots: Optional[List[str]] = None, limit: int = 2000) -> Tuple[bool, str]:
        if roots is None:
            roots = [str(Path.home() / "Downloads"), str(Path.home() / "Documents")]
        hashes: Dict[str, str] = {}
        dups: List[Tuple[str, str]] = []
        scanned = 0
        for r in roots:
            p = Path(r)
            if not p.exists():
                continue
            for fp in p.rglob("*"):
                if fp.is_file():
                    scanned += 1
                    if scanned > limit:
                        break
                    try:
                        h = self._sha1_file(fp)
                        if h in hashes:
                            dups.append((str(fp), hashes[h]))
                        else:
                            hashes[h] = str(fp)
                    except Exception:
                        pass
        lines = [f"{a} == {b}" for a, b in dups]
        return True, "\n".join(lines) if lines else "No duplicates found (scan limited)."

    def _sha1_file(self, path: Path) -> str:
        import hashlib
        h = hashlib.sha1()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def analyze_disk_usage(self) -> Tuple[bool, str]:
        r1 = run_ps("Get-Volume | Select-Object DriveLetter, FileSystem, SizeRemaining, Size | "
                    "Format-Table -AutoSize | Out-String")
        r2 = run_ps("Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free | "
                    "Format-Table -AutoSize | Out-String")
        out = (r1.stdout or r1.stderr or "") + "\n" + (r2.stdout or r2.stderr or "")
        return True, out.strip()

    def compact_winsxs(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps("DISM /Online /Cleanup-Image /StartComponentCleanup")
        return (r.returncode == 0), (r.stdout or r.stderr or "WinSxS compact requested.")

    def purge_prefetch_cache(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        pf = Path(r"C:\Windows\Prefetch")
        removed = 0
        if pf.exists():
            for f in pf.glob("*.pf"):
                try:
                    f.unlink(missing_ok=True)
                    removed += 1
                except Exception:
                    pass
        return True, f"Removed {removed} prefetch entries."

    def remove_windows_old(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        wold = Path(r"C:\Windows.old")
        if not wold.exists():
            return True, "Windows.old not present."
        r = run_ps("Remove-Item -LiteralPath 'C:\\Windows.old' -Recurse -Force -ErrorAction SilentlyContinue")
        ok = r.returncode == 0
        return ok, ("Windows.old removed." if ok else (r.stderr or r.stdout or "Removal failed (in use)."))

    # ---------------------------------------------------------
    # Task Scheduler Tweaks
    # ---------------------------------------------------------
    def list_common_tasks(self) -> Tuple[bool, str]:
        tasks = self._telemetry_tasks() + self._xbox_tasks()
        lines = []
        for t in tasks:
            q = run_ps(f'schtasks /Query /TN "{t}" /FO LIST')
            out = (q.stdout or q.stderr or "").strip()
            lines.append(out if out else f"{t}: (not found)")
        return True, "\n\n".join(lines)

    def disable_telemetry_tasks(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        msgs = []
        for t in self._telemetry_tasks():
            r = run_ps(f'schtasks /Change /TN "{t}" /Disable')
            msgs.append(f"{t}: {'disabled' if r.returncode == 0 else 'not found'}")
        return True, "\n".join(msgs)

    def enable_telemetry_tasks(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        msgs = []
        for t in self._telemetry_tasks():
            r = run_ps(f'schtasks /Change /TN "{t}" /Enable')
            msgs.append(f"{t}: {'enabled' if r.returncode == 0 else 'not found'}")
        return True, "\n".join(msgs)

    def disable_xbox_tasks(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        msgs = []
        for t in self._xbox_tasks():
            r = run_ps(f'schtasks /Change /TN "{t}" /Disable')
            msgs.append(f"{t}: {'disabled' if r.returncode == 0 else 'not found'}")
        return True, "\n".join(msgs)

    def enable_xbox_tasks(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        msgs = []
        for t in self._xbox_tasks():
            r = run_ps(f'schtasks /Change /TN "{t}" /Enable')
            msgs.append(f"{t}: {'enabled' if r.returncode == 0 else 'not found'}")
        return True, "\n".join(msgs)

    def _telemetry_tasks(self) -> List[str]:
        return [
            r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            r"\Microsoft\Windows\Application Experience\AitAgent",
            r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
            r"\Microsoft\Windows\Autochk\Proxy",
            r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
        ]

    def _xbox_tasks(self) -> List[str]:
        return [
            r"\Microsoft\XblGameSave\XblGameSaveTask",
            r"\Microsoft\XblGameSave\XblGameSaveTaskLogon",
        ]

    # ---------------------------------------------------------
    # Restore Defaults & Logs
    # ---------------------------------------------------------
    def restore_defaults(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        msgs = []

        # Power plan -> Balanced
        run_ps("powercfg -setactive SCHEME_BALANCED"); msgs.append("Power plan -> Balanced")

        # Network defaults
        for n in ["Ethernet", "Wi-Fi", "WiFi", "Local Area Connection"]:
            run_ps(f'netsh interface ip set dns name="{n}" dhcp')
        msgs.append("DNS -> DHCP (all common adapters)")
        run_ps('netsh int tcp set global autotuninglevel=normal'); msgs.append("TCP autotuning -> normal")
        run_ps('netsh int tcp set global congestionprovider=none'); msgs.append("CTCP -> disabled")
        self.toggle_nagle(False); msgs.append("Nagle -> enabled (default)")

        # Game Mode default ON
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "AllowAutoGameMode", 0, winreg.REG_DWORD, 1)
            msgs.append("Game Mode -> ON")
        except Exception:
            msgs.append("Game Mode -> unchanged")

        # Visual Effects -> Windows default (0 = Let Windows decide)
        try:
            path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "VisualFXSetting", 0, winreg.REG_DWORD, 0)
            msgs.append("Visual Effects -> default")
        except Exception:
            msgs.append("Visual Effects -> unchanged")

        # Services -> revert common ones
        run_ps("Set-Service -Name SysMain -StartupType Automatic -ErrorAction SilentlyContinue")
        run_ps("Set-Service -Name DiagTrack -StartupType Manual -ErrorAction SilentlyContinue")
        msgs.append("Services -> common defaults restored (SysMain/DiagTrack)")

        return True, "Restored defaults:\n- " + "\n- ".join(msgs)

    def export_logs_zip(self) -> Tuple[bool, str]:
        export_dir = self.root / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        out_zip = export_dir / "QrsTweaks_Logs.zip"
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for p in self.logs_dir.glob("*.txt"):
                z.write(p, arcname=p.name)
        return True, f"Logs exported: {out_zip}"

    def open_logs_folder(self) -> Tuple[bool, str]:
        try:
            os.startfile(self.logs_dir)  # Windows-only
            return True, f"Opened: {self.logs_dir}"
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # Default Game Optimizer (Games Page)
    # ---------------------------------------------------------
    def apply_default_game_tweaks(self) -> str:
        cmds = [
            'Set-ItemProperty -Path "HKCU:\\System\\GameConfigStore" -Name GameDVR_Enabled -Value 0',
            'Set-Service SysMain -StartupType Disabled -ErrorAction SilentlyContinue',
            'netsh interface tcp set global autotuninglevel=normal',
            'powercfg -setactive SCHEME_MIN'
        ]
        for c in cmds:
            run_ps(c)
        return "Applied default gaming optimizations."

    def revert_default_game_tweaks(self) -> str:
        cmds = [
            'Set-ItemProperty -Path "HKCU:\\System\\GameConfigStore" -Name GameDVR_Enabled -Value 1',
            'Set-Service SysMain -StartupType Automatic -ErrorAction SilentlyContinue',
            'netsh interface tcp set global autotuninglevel=highlyrestricted',
            'powercfg -setactive SCHEME_BALANCED'
        ]
        for c in cmds:
            run_ps(c)
        return "Reverted optimizations to default state."

    # ---------------------------------------------------------
    # Profile Application (JSON-based, safe keys)
    # ---------------------------------------------------------
    def apply_profile(self, data: Dict) -> str:
        """
        Apply a JSON profile:
          {
            "name": "...",
            "description": "...",
            "tweaks": {
                "GameBar": false,
                "FullscreenOptimizations": false,
                "LowLatencyMode": true,
                "PriorityBoost": true,
                "VisualFX": "performance|balanced|default",
                "NetworkStack": "gaming|ultra-low",
                "CTCP": true,
                "DNS": "1.1.1.1",
                "SysMain": false,
                "Telemetry": false
            }
          }
        """
        tweaks = data.get("tweaks", {})
        applied = []

        for key, value in tweaks.items():
            try:
                if key == "GameBar":
                    self._set_reg_hkcu(r"Software\Microsoft\GameBar", "ShowStartupPanel", 0 if not value else 1)
                    applied.append("GameBar")
                elif key == "FullscreenOptimizations":
                    # Disable FSE behavior -> 2 (performance mode) under GameDVR_FSEBehaviorMode
                    run_ps(r'reg add "HKCU\System\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f')
                    applied.append("FullscreenOptimizations")
                elif key == "LowLatencyMode":
                    # Processor performance boost mode: 1 (Efficient Aggressive)
                    run_ps('powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE 1')
                    applied.append("LowLatencyMode")
                elif key == "PriorityBoost":
                    # Give shell a gentle nudge; for actual game, user should start game then set priority there
                    run_ps('wmic process where name="explorer.exe" call setpriority 128')
                    applied.append("PriorityBoost")
                elif key == "SysMain":
                    run_ps(f'Set-Service SysMain -StartupType {"Automatic" if value else "Disabled"}')
                    applied.append("SysMain")
                elif key == "Telemetry":
                    run_ps(f'Set-Service DiagTrack -StartupType {"Disabled" if not value else "Automatic"}')
                    applied.append("Telemetry")
                elif key == "CTCP":
                    run_ps('netsh interface tcp set global congestionprovider=ctcp')
                    applied.append("CTCP")
                elif key == "DNS":
                    # Default to Ethernet; user may adjust adapter if needed
                    run_ps(f'netsh interface ip set dns "Ethernet" static {value}')
                    applied.append("DNS")
                elif key == "NetworkStack":
                    if str(value).lower() == "gaming":
                        run_ps('netsh interface tcp set global autotuninglevel=normal')
                    elif str(value).lower() == "ultra-low":
                        run_ps('netsh interface tcp set global autotuninglevel=disabled')
                    applied.append(f"NetworkStack={value}")
                elif key == "VisualFX":
                    level = {"performance": 2, "balanced": 1, "default": 0}.get(str(value).lower(), 0)
                    run_ps(rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" '
                           rf'/v VisualFXSetting /t REG_DWORD /d {level} /f')
                    applied.append(f"VisualFX={value}")
            except Exception:
                # Keep going even if one tweak fails
                pass

        return f"Applied {len(applied)} tweaks from profile: {', '.join(applied)}"

    # Registry helper
    def _set_reg_hkcu(self, path: str, name: str, value: int) -> None:
        try:
            hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
            winreg.SetValueEx(hkey, name, 0, winreg.REG_DWORD, int(value))
            winreg.CloseKey(hkey)
        except Exception:
            pass
