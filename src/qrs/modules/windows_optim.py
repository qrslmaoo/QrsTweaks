# src/qrs/modules/windows_optim.py
from __future__ import annotations

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

import psutil
import winreg


# ---------------- Utilities ----------------
def is_admin() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(script: str) -> subprocess.CompletedProcess:
    """Run PowerShell inline, capture output, no new window."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        text=True, capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def run_ps_elevated_blocking(script: str) -> bool:
    """Request elevation, run script in a new PowerShell as admin, wait for completion."""
    esc = script.replace("'", "''")
    wrapper = (
        "Start-Process powershell -Verb RunAs "
        f"'-NoProfile -ExecutionPolicy Bypass -Command \"{esc}\"' -Wait"
    )
    r = run_ps(wrapper)
    return r.returncode == 0


def bytes_fmt(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def dir_size_and_count(path: Path) -> Tuple[int, int]:
    total = 0
    count = 0
    if not path.exists():
        return 0, 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
                count += 1
            except Exception:
                pass
    return total, count


class WindowsOptimizer:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.logs_dir = self.root / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._memleak_proc_name = "qrs_memguard.exe"

    # ---------------- System scan ----------------
    def quick_scan(self) -> str:
        targets = [
            (Path(os.getenv("TEMP") or r"C:\Windows\Temp"), "User Temp"),
            (Path(r"C:\Windows\Temp"), "System Temp"),
            (Path(r"C:\Windows\Prefetch"), "Prefetch"),
            (Path(r"C:\Windows\SoftwareDistribution\Download"), "Windows Update Cache"),
        ]
        total_bytes = 0
        total_files = 0
        report = []

        for p, label in targets:
            size, cnt = dir_size_and_count(p)
            total_bytes += size; total_files += cnt
            report.append(f"[{label}] {cnt:,} files ({bytes_fmt(size)})")

        # Recycle Bin estimate
        try:
            ps = r"(New-Object -ComObject Shell.Application).NameSpace(10).Items() | " \
                 r"Measure-Object -Property Size -Sum | Select-Object -ExpandProperty Sum"
            rb = run_ps(ps)
            if rb.returncode == 0 and rb.stdout.strip():
                rb_size = int(rb.stdout.strip())
                total_bytes += rb_size
                report.append(f"[Recycle Bin] ~{bytes_fmt(rb_size)}")
        except Exception:
            report.append("[Recycle Bin] size unavailable")

        report.append("")
        report.append(f"[Scan Complete] {total_files:,} files detected.")
        report.append(f"Estimated cleanable space: {bytes_fmt(total_bytes)}")
        return "\n".join(report)

    # ---------------- Status helpers (already used elsewhere) ----------------
    def is_high_perf_plan(self) -> bool:
        try:
            output = subprocess.check_output(["powercfg", "/getactivescheme"], text=True).lower()
            return ("high performance" in output) or ("ultimate performance" in output) or ("scheme_min" in output)
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
                return int(val) == 2
        except Exception:
            return False

    def is_network_optimized(self) -> bool:
        try:
            out = subprocess.check_output(["netsh", "int", "tcp", "show", "global"], text=True).lower()
            ctcp_ok = ("congestion provider" in out and "ctcp" in out)
            tuned = ("autotuning" in out and ("restricted" in out or "disabled" in out))
            return ctcp_ok or tuned
        except Exception:
            return False

    def is_memleak_guard_active(self) -> bool:
        try:
            for p in psutil.process_iter(["name"]):
                if (p.info.get("name") or "").lower() == self._memleak_proc_name:
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
            names = {d.get("Name"): (str(d.get("StartType", "")).lower(), str(d.get("Status", "")).lower()) for d in data}
            sysmain_ok = ("SysMain" in names) and (names["SysMain"][0] == "disabled")
            diag_ok = ("DiagTrack" in names) and (names["DiagTrack"][0] == "disabled")
            return sysmain_ok and diag_ok
        except Exception:
            return False

    # ---------------- Basic actions ----------------
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
        tmp_targets = [Path(os.environ.get("TEMP", r"C:\Windows\Temp")), Path(r"C:\Windows\Temp")]
        count = 0
        for base in tmp_targets:
            if not base.exists():
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    try:
                        (Path(root) / f).unlink(missing_ok=True)
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

    # ---------------- Network helpers ----------------
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

    # ---------------- Deep Cleanup (existing) ----------------
    def _delete_tree_best_effort(self, path: Path) -> Tuple[int, int]:
        files = 0
        bytes_sum = 0
        if not path.exists():
            return 0, 0
        for root, dirs, fs in os.walk(path, topdown=False):
            for f in fs:
                fp = Path(root) / f
                try:
                    size = fp.stat().st_size
                    fp.unlink(missing_ok=True)
                    files += 1
                    bytes_sum += size
                except Exception:
                    pass
            for d in dirs:
                dp = Path(root) / d
                try:
                    dp.rmdir()
                except Exception:
                    pass
        return files, bytes_sum

    def cleanup_browser_caches(self) -> Tuple[bool, str]:
        home = Path.home()
        targets = [
            home / "AppData/Local/Google/Chrome/User Data/Default/Cache",
            home / "AppData/Local/Google/Chrome/User Data/Default/Code Cache",
            home / "AppData/Local/Microsoft/Edge/User Data/Default/Cache",
            home / "AppData/Local/Microsoft/Edge/User Data/Default/Code Cache",
            home / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Cache",
            home / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Code Cache",
        ]
        ff_root = home / "AppData/Roaming/Mozilla/Firefox/Profiles"
        if ff_root.exists():
            for prof in ff_root.glob("*.default*"):
                targets.append(prof / "cache2")

        removed_files = 0
        reclaimed = 0
        for t in targets:
            f, b = self._delete_tree_best_effort(t)
            removed_files += f
            reclaimed += b
        return True, f"Browser caches cleaned: {removed_files:,} files, {bytes_fmt(reclaimed)} reclaimed."

    def cleanup_prefetch_and_logs(self) -> Tuple[bool, str]:
        targets = [Path(r"C:\Windows\Prefetch"), Path(r"C:\Windows\Logs")]
        removed_files = 0
        reclaimed = 0
        for t in targets:
            f, b = self._delete_tree_best_effort(t)
            removed_files += f
            reclaimed += b
        return True, f"Prefetch & Logs cleaned: {removed_files:,} files, {bytes_fmt(reclaimed)} reclaimed."

    def cleanup_windows_old(self) -> Tuple[bool, str]:
        target = Path(r"C:\Windows.old")
        if not target.exists():
            return True, "Windows.old not present."
        if not is_admin():
            ps = r"Remove-Item -LiteralPath 'C:\Windows.old' -Recurse -Force -ErrorAction SilentlyContinue"
            ok = run_ps_elevated_blocking(ps)
            return ok, "Windows.old removal requested with elevation." if ok else "Windows.old removal failed."
        files, size = self._delete_tree_best_effort(target)
        try:
            target.rmdir()
        except Exception:
            pass
        return True, f"Windows.old cleaned: {files:,} files, {bytes_fmt(size)} reclaimed (best-effort)."

    def cleanup_deep(self) -> Tuple[bool, str]:
        summaries = []
        total_files = 0
        total_bytes = 0

        ok, msg = self.cleanup_browser_caches()
        summaries.append(msg); total_files += self._parse_first_int(msg); total_bytes += self._parse_bytes_in_msg(msg)

        ok, msg = self.cleanup_prefetch_and_logs()
        summaries.append(msg); total_files += self._parse_first_int(msg); total_bytes += self._parse_bytes_in_msg(msg)

        ok, msg = self.cleanup_windows_old()
        summaries.append(msg); total_files += self._parse_first_int(msg); total_bytes += self._parse_bytes_in_msg(msg)

        summaries.append("")
        summaries.append(f"[Summary] Total removed files: {total_files:,}")
        summaries.append(f"[Summary] Total reclaimed: {bytes_fmt(total_bytes)}")
        return True, "\n".join(summaries)

    def _parse_first_int(self, text: str) -> int:
        import re
        m = re.search(r"([0-9][0-9,]*)\s+files", text, re.IGNORECASE)
        if not m:
            return 0
        try:
            return int(m.group(1).replace(",", ""))
        except Exception:
            return 0

    def _parse_bytes_in_msg(self, text: str) -> int:
        import re
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(KB|MB|GB|TB)", text, re.IGNORECASE)
        if not m:
            return 0
        val = float(m.group(1)); unit = m.group(2).upper()
        mult = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}.get(unit, 1)
        return int(val * mult)

    # ---------------- Storage Tools ----------------
    def _excluded_dirs(self) -> List[str]:
        return [r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)"]

    def _should_skip_dir(self, abspath: str) -> bool:
        abspath_norm = abspath.rstrip("\\").lower()
        for ex in self._excluded_dirs():
            if abspath_norm.startswith(ex.lower()):
                return True
        bad_names = {"system volume information", "$recycle.bin", "windowsapps"}
        tail = os.path.basename(abspath_norm)
        if tail in bad_names:
            return True
        return False

    def analyze_largest_files(self, limit: int = 25) -> Tuple[bool, str]:
        root = r"C:\\"
        results: List[Tuple[int, str]] = []
        for current_root, dirs, files in os.walk(root, topdown=True):
            try:
                dirs[:] = [d for d in dirs if not self._should_skip_dir(os.path.join(current_root, d))]
            except Exception:
                dirs[:] = []
            for f in files:
                fp = os.path.join(current_root, f)
                try:
                    if os.path.islink(fp):
                        continue
                    size = os.stat(fp, follow_symlinks=False).st_size
                    results.append((size, fp))
                except Exception:
                    pass
        results.sort(reverse=True)
        top = results[:limit]
        if not top:
            return True, "[Storage] No files enumerated."
        total = sum(sz for sz, _ in top)
        lines = ["[Storage] Largest Files (Top {}):".format(limit)]
        for sz, path in top:
            lines.append(f"  - {bytes_fmt(sz):>10} — {path}")
        lines.append(f"[Storage] Total (top {limit}): {bytes_fmt(total)}")
        return True, "\n".join(lines)

    def analyze_top_dirs(self, limit: int = 10) -> Tuple[bool, str]:
        from collections import defaultdict
        root = r"C:\\"
        by_toplevel = defaultdict(int)

        def top_key(path: str) -> str:
            p = Path(path)
            parts = p.parts
            if len(parts) >= 2:
                return str(Path(parts[0]) / parts[1])
            return str(p)

        for current_root, dirs, files in os.walk(root, topdown=True):
            try:
                dirs[:] = [d for d in dirs if not self._should_skip_dir(os.path.join(current_root, d))]
            except Exception:
                dirs[:] = []
            key = top_key(current_root)
            for f in files:
                fp = os.path.join(current_root, f)
                try:
                    if os.path.islink(fp):
                        continue
                    by_toplevel[key] += os.stat(fp, follow_symlinks=False).st_size
                except Exception:
                    pass

        for ex in self._excluded_dirs():
            by_toplevel.pop(ex, None)

        ranked = sorted(by_toplevel.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        if not ranked:
            return True, "[Storage] No directory data."
        lines = ["[Storage] Top Directories (by total size):"]
        for path, sz in ranked:
            lines.append(f"  - {bytes_fmt(sz):>10} — {path}")
        return True, "\n".join(lines)

    def optimize_ssd_trim(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps("defrag /C /L")
        return (r.returncode == 0), (r.stdout or r.stderr or "SSD TRIM executed.")

    def optimize_hdd_defrag(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        r = run_ps("defrag /A /U /V")
        ok = (r.returncode == 0)
        return ok, (r.stdout or r.stderr or "Defrag completed.")

    def cleanup_windows_updates(self) -> Tuple[bool, str]:
        if not is_admin():
            return False, "Admin required."
        lines = []
        def _wipe(p: str):
            f = run_ps(f"Remove-Item -LiteralPath '{p}' -Recurse -Force -ErrorAction SilentlyContinue")
            return "OK" if f.returncode == 0 else "Skipped"

        do_cache = r"C:\ProgramData\Microsoft\Windows\DeliveryOptimization\Cache"
        lines.append(f"Delivery Optimization cache: {_wipe(do_cache)}")

        sw = r"C:\Windows\SoftwareDistribution\Download"
        lines.append(f"Windows Update cache: {_wipe(sw)}")

        d1 = run_ps("DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase")
        lines.append("DISM StartComponentCleanup: " + ("OK" if d1.returncode == 0 else "Failed"))
        d2 = run_ps("Dism.exe /Online /Cleanup-Image /SPSuperseded")
        lines.append("SPSuperseded: " + ("OK" if d2.returncode == 0 else "Skipped/Not applicable."))
        return True, "[Windows Update Cleanup]\n- " + "\n- ".join(lines)

    def check_drive_health(self) -> Tuple[bool, str]:
        try:
            ps = r"(Get-PhysicalDisk | Select-Object FriendlyName,HealthStatus,MediaType,Size | ConvertTo-Json)"
            r = run_ps(ps)
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                if isinstance(data, dict):
                    data = [data]
                lines = ["[Drive Health]"]
                for d in data:
                    name = d.get("FriendlyName", "Disk")
                    health = d.get("HealthStatus", "Unknown")
                    mtype = d.get("MediaType", "Unknown")
                    size = int(d.get("Size") or 0)
                    lines.append(f"  - {name}: {health} | {mtype} | {bytes_fmt(size)}")
                return True, "\n".join(lines)
        except Exception:
            pass
        try:
            out = subprocess.check_output(["wmic", "diskdrive", "get", "status,model,size"], text=True)
            lines = ["[Drive Health] (WMIC)"]
            for ln in out.splitlines():
                ln = ln.strip()
                if not ln or ln.lower().startswith("status"):
                    continue
                lines.append("  - " + ln)
            return True, "\n".join(lines) if len(lines) > 1 else "[Drive Health] No data."
        except Exception as e:
            return False, f"[Drive Health] Failed: {e}"

    # ---------------- Gaming/Profile helpers ----------------
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

    # ---------------- Phase 3: System Optimization ----------------
    def apply_system_tweaks(self) -> Tuple[bool, str]:
        script = r"""
$svcs = @('SysMain','DiagTrack','dmwappushsvc')
foreach ($n in $svcs) {
  $svc = Get-Service -Name $n -ErrorAction SilentlyContinue
  if ($svc) {
    try {
      Set-Service -Name $n -StartupType Disabled -ErrorAction SilentlyContinue
      if ($svc.Status -eq 'Running') { Stop-Service -Name $n -Force -ErrorAction SilentlyContinue }
    } catch {}
  }
}
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Name 'AllowTelemetry' -Type DWord -Value 0
New-Item -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting' -Name 'Disabled' -Type DWord -Value 1
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy' -Name 'LetAppsRunInBackground' -Type DWord -Value 2
New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Name 'VisualFXSetting' -Type DWord -Value 2
"""
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            return ok, "Applied recommended system tweaks." if ok else (r.stderr or r.stdout or "Failed to apply tweaks.")
        else:
            ok = run_ps_elevated_blocking(script)
            return ok, "Applied recommended system tweaks (elevated)." if ok else "Failed (UAC denied or script error)."

    def revert_system_defaults(self) -> Tuple[bool, str]:
        script = r"""
$svcs = @('SysMain','DiagTrack','dmwappushsvc')
foreach ($n in $svcs) {
  $svc = Get-Service -Name $n -ErrorAction SilentlyContinue
  if ($svc) {
    try {
      $start = 'Automatic'
      if ($n -eq 'DiagTrack') { $start = 'Manual' }
      Set-Service -Name $n -StartupType $start -ErrorAction SilentlyContinue
      if ($svc.Status -ne 'Running' -and $start -eq 'Automatic') { Start-Service -Name $n -ErrorAction SilentlyContinue }
    } catch {}
  }
}
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' -Name 'AllowTelemetry' -Type DWord -Value 3
New-Item -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting' -Name 'Disabled' -Type DWord -Value 0
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy' -Name 'LetAppsRunInBackground' -Type DWord -Value 1
New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Name 'VisualFXSetting' -Type DWord -Value 0
"""
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            return ok, "Restored default Windows settings." if ok else (r.stderr or r.stdout or "Failed to revert.")
        else:
            ok = run_ps_elevated_blocking(script)
            return ok, "Restored default Windows settings (elevated)." if ok else "Failed (UAC denied or script error)."

    def apply_gaming_mode(self) -> Tuple[bool, str]:
        script = r"""
powercfg -setactive SCHEME_MIN | Out-Null
New-Item -Path 'HKCU:\System\GameConfigStore' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -Type DWord -Value 0
New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Name 'AppCaptureEnabled' -Type DWord -Value 0
New-Item -Path 'HKCU:\Software\Microsoft\GameBar' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'ShowStartupPanel' -Type DWord -Value 0
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'UseNexus' -Type DWord -Value 0
netsh int tcp set global congestionprovider=ctcp | Out-Null
netsh int tcp set global autotuninglevel=normal | Out-Null
$svc = Get-Service -Name 'SysMain' -ErrorAction SilentlyContinue
if ($svc) {
  Set-Service -Name 'SysMain' -StartupType Disabled -ErrorAction SilentlyContinue
  if ($svc.Status -eq 'Running') { Stop-Service -Name 'SysMain' -Force -ErrorAction SilentlyContinue }
}
"""
        nagle_ok = True
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            n_ok, _ = self.toggle_nagle(True)
            nagle_ok = n_ok
            return (ok and nagle_ok), "Gaming Mode applied."
        else:
            ok = run_ps_elevated_blocking(script)
            if ok:
                run_ps_elevated_blocking("Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces' | "
                                         "ForEach-Object { New-ItemProperty -Path $_.PsPath -Name 'TcpNoDelay' -Value 1 -PropertyType DWord -Force; "
                                         "New-ItemProperty -Path $_.PsPath -Name 'TcpAckFrequency' -Value 1 -PropertyType DWord -Force }")
            return ok, "Gaming Mode applied (elevated)." if ok else "Failed to apply Gaming Mode."

    def revert_normal_mode(self) -> Tuple[bool, str]:
        script = r"""
powercfg -setactive SCHEME_BALANCED | Out-Null
New-Item -Path 'HKCU:\System\GameConfigStore' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -Type DWord -Value 1
New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Name 'AppCaptureEnabled' -Type DWord -Value 1
New-Item -Path 'HKCU:\Software\Microsoft\GameBar' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'ShowStartupPanel' -Type DWord -Value 1
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'UseNexus' -Type DWord -Value 1
netsh int tcp set global congestionprovider=none | Out-Null
netsh int tcp set global autotuninglevel=normal | Out-Null
$svc = Get-Service -Name 'SysMain' -ErrorAction SilentlyContinue
if ($svc) {
  Set-Service -Name 'SysMain' -StartupType Automatic -ErrorAction SilentlyContinue
  if ($svc.Status -ne 'Running') { Start-Service -Name 'SysMain' -ErrorAction SilentlyContinue }
}
"""
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            self.toggle_nagle(False)
            return ok, "Reverted to Normal Mode." if ok else (r.stderr or r.stdout or "Failed to revert.")
        else:
            ok = run_ps_elevated_blocking(script)
            if ok:
                run_ps_elevated_blocking("Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces' | "
                                         "ForEach-Object { New-ItemProperty -Path $_.PsPath -Name 'TcpNoDelay' -Value 0 -PropertyType DWord -Force; "
                                         "New-ItemProperty -Path $_.PsPath -Name 'TcpAckFrequency' -Value 0 -PropertyType DWord -Force }")
            return ok, "Reverted to Normal Mode (elevated)." if ok else "Failed to revert."

    # ======================================================================
    # Phase 4: Startup & Background Services
    # ======================================================================

    # ---- Startup helpers ----
    def _startup_keys(self):
        return [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]

    def _disabled_key_path(self, base: str) -> str:
        return base.replace("\\Run", "\\Run-Disabled-QrsTweaks")

    def _ensure_key(self, root, path):
        try:
            winreg.CreateKey(root, path)
        except Exception:
            pass

    def _startup_folders(self) -> List[Path]:
        user_startup = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
        common_startup = Path(os.environ.get("ProgramData", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
        return [p for p in [user_startup, common_startup] if p and p.exists()]

    def _disabled_startup_folder(self, startup_folder: Path) -> Path:
        return startup_folder.parent / "Startup (Disabled by QrsTweaks)"

    def _is_allowlisted(self, name: str, val: str) -> bool:
        name_l = (name or "").lower()
        val_l = (val or "").lower()
        allow = [
            "securityhealth", "defender", "msascui", "ctfmon",
            "realtek", "nahimic", "audio", "sound", "rtk",
            "nvidia", "nvbackend", "igfx", "intelgraphics", "amd", "radeon",
        ]
        return any(a in name_l or a in val_l for a in allow)

    def list_startup_entries_detailed(self) -> Tuple[bool, str]:
        lines = ["[Startup] Entries:"]
        # Registry
        for root, path in self._startup_keys():
            try:
                with winreg.OpenKey(root, path) as k:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(k, i); i += 1
                            lines.append(f"  - REG  @{path} :: {name} => {val}")
                        except OSError:
                            break
            except FileNotFoundError:
                pass

        # Startup folders
        for folder in self._startup_folders():
            try:
                for item in folder.iterdir():
                    if item.name.lower() == "desktop.ini":
                        continue
                    lines.append(f"  - FILE @{folder} :: {item.name} => {item}")
            except Exception:
                pass

        if len(lines) == 1:
            lines.append("  (none)")
        return True, "\n".join(lines)

    def disable_startup_auto(self) -> Tuple[bool, str]:
        """Disable non-essential startup entries: move from Run -> Run-Disabled-QrsTweaks and move files."""
        if not is_admin():
            ok = run_ps_elevated_blocking("Write-Host 'elevating for startup changes'")
            if not ok:
                return False, "Admin required to disable startup entries."

        moved = 0
        # Registry: move values to disabled key if not allowlisted
        for root, base in self._startup_keys():
            disabled = self._disabled_key_path(base)
            self._ensure_key(root, disabled)
            try:
                with winreg.OpenKey(root, base) as k:
                    # collect first to avoid editing while enumerating
                    entries = []
                    i = 0
                    while True:
                        try:
                            name, val, typ = winreg.EnumValue(k, i); i += 1
                            entries.append((name, val, typ))
                        except OSError:
                            break
            except FileNotFoundError:
                entries = []

            for name, val, typ in entries:
                if self._is_allowlisted(name, val):
                    continue
                try:
                    with winreg.OpenKey(root, disabled, 0, winreg.KEY_SET_VALUE) as kd:
                        winreg.SetValueEx(kd, name, 0, typ, val)
                    with winreg.OpenKey(root, base, 0, winreg.KEY_SET_VALUE) as kb:
                        try:
                            winreg.DeleteValue(kb, name)
                        except FileNotFoundError:
                            pass
                    moved += 1
                except Exception:
                    pass

        # Startup folders: move files to "Startup (Disabled by QrsTweaks)"
        for folder in self._startup_folders():
            disabled_folder = self._disabled_startup_folder(folder)
            disabled_folder.mkdir(parents=True, exist_ok=True)
            try:
                for item in list(folder.iterdir()):
                    if item.name.lower() == "desktop.ini":
                        continue
                    try:
                        shutil.move(str(item), str(disabled_folder / item.name))
                        moved += 1
                    except Exception:
                        pass
            except Exception:
                pass

        return True, f"Disabled {moved} startup item(s)."

    def enable_startup_disabled(self) -> Tuple[bool, str]:
        """Re-enable items previously disabled by QrsTweaks."""
        if not is_admin():
            ok = run_ps_elevated_blocking("Write-Host 'elevating for startup changes'")
            if not ok:
                return False, "Admin required to enable startup entries."

        restored = 0
        # Registry: move values back from Run-Disabled-QrsTweaks -> Run
        for root, base in self._startup_keys():
            disabled = self._disabled_key_path(base)
            try:
                with winreg.OpenKey(root, disabled) as k:
                    entries = []
                    i = 0
                    while True:
                        try:
                            name, val, typ = winreg.EnumValue(k, i); i += 1
                            entries.append((name, val, typ))
                        except OSError:
                            break
            except FileNotFoundError:
                entries = []

            for name, val, typ in entries:
                try:
                    with winreg.OpenKey(root, base, 0, winreg.KEY_SET_VALUE) as kb:
                        winreg.SetValueEx(kb, name, 0, typ, val)
                    with winreg.OpenKey(root, disabled, 0, winreg.KEY_SET_VALUE) as kd:
                        try:
                            winreg.DeleteValue(kd, name)
                        except FileNotFoundError:
                            pass
                    restored += 1
                except Exception:
                    pass

        # Startup folders: move files back
        for folder in self._startup_folders():
            disabled_folder = self._disabled_startup_folder(folder)
            if not disabled_folder.exists():
                continue
            try:
                for item in list(disabled_folder.iterdir()):
                    try:
                        shutil.move(str(item), str(folder / item.name))
                        restored += 1
                    except Exception:
                        pass
            except Exception:
                pass

        return True, f"Re-enabled {restored} startup item(s)."

    def remove_startup_disabled(self) -> Tuple[bool, str]:
        """Permanently delete items previously disabled by QrsTweaks (registry & files)."""
        if not is_admin():
            ok = run_ps_elevated_blocking("Write-Host 'elevating for startup changes'")
            if not ok:
                return False, "Admin required to remove startup entries."

        removed = 0
        # Registry: delete values under Run-Disabled-QrsTweaks
        for root, base in self._startup_keys():
            disabled = self._disabled_key_path(base)
            try:
                with winreg.OpenKey(root, disabled) as k:
                    names = []
                    i = 0
                    while True:
                        try:
                            name, _, _ = winreg.EnumValue(k, i); i += 1
                            names.append(name)
                        except OSError:
                            break
            except FileNotFoundError:
                names = []

            for name in names:
                try:
                    with winreg.OpenKey(root, disabled, 0, winreg.KEY_SET_VALUE) as kd:
                        winreg.DeleteValue(kd, name)
                        removed += 1
                except Exception:
                    pass

        # Startup folders: delete files in "Startup (Disabled by QrsTweaks)"
        for folder in self._startup_folders():
            disabled_folder = self._disabled_startup_folder(folder)
            if not disabled_folder.exists():
                continue
            try:
                for item in list(disabled_folder.iterdir()):
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                        removed += 1
                    except Exception:
                        pass
            except Exception:
                pass

        return True, f"Permanently removed {removed} disabled startup item(s)."

    # ---- Background Services ----
    def list_heavy_services(self) -> Tuple[bool, str]:
        """Return a summary of known heavy/optional services and their states."""
        names = [
            "SysMain", "WSearch", "DiagTrack", "dmwappushsvc",
            "MapsBroker", "WMPNetworkSvc", "WerSvc"
        ]
        ps = (
            "$n=@('SysMain','WSearch','DiagTrack','dmwappushsvc','MapsBroker','WMPNetworkSvc','WerSvc');"
            "Get-Service -Name $n -ErrorAction SilentlyContinue | "
            "Select-Object Name,Status,StartType | ConvertTo-Json"
        )
        r = run_ps(ps)
        lines = ["[Services] Heavy/Optional services:"]
        if r.returncode == 0 and r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                if isinstance(data, dict):
                    data = [data]
                for d in data:
                    lines.append(f"  - {d.get('Name')} | {d.get('Status')} | {d.get('StartType')}")
            except Exception:
                lines.append("  (Unable to parse service info.)")
        else:
            lines.append("  (No data)")
        return True, "\n".join(lines)

    def disable_non_essential_services(self) -> Tuple[bool, str]:
        """Disable + stop a curated set of non-essential services (safe default list)."""
        script = r"""
$n = @('SysMain','WSearch','DiagTrack','dmwappushsvc','MapsBroker','WMPNetworkSvc','WerSvc')
foreach ($svc in $n) {
  $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
  if ($s) {
    try {
      Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
      if ($s.Status -eq 'Running') { Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue }
    } catch {}
  }
}
"""
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            return ok, "Disabled non-essential services." if ok else (r.stderr or r.stdout or "Failed to disable services.")
        else:
            ok = run_ps_elevated_blocking(script)
            return ok, "Disabled non-essential services (elevated)." if ok else "Failed (UAC denied)."

    def restore_default_services(self) -> Tuple[bool, str]:
        """Restore default-ish startup types for the curated list."""
        # Approximate defaults: SysMain Auto, WSearch Auto, DiagTrack Manual, dmwappushsvc Manual,
        # MapsBroker Manual, WMPNetworkSvc Manual, WerSvc Manual
        script = r"""
$defaults = @{
  'SysMain'='Automatic'
  'WSearch'='Automatic'
  'DiagTrack'='Manual'
  'dmwappushsvc'='Manual'
  'MapsBroker'='Manual'
  'WMPNetworkSvc'='Manual'
  'WerSvc'='Manual'
}
foreach ($pair in $defaults.GetEnumerator()) {
  $n = $pair.Key; $t = $pair.Value
  $s = Get-Service -Name $n -ErrorAction SilentlyContinue
  if ($s) {
    try {
      Set-Service -Name $n -StartupType $t -ErrorAction SilentlyContinue
      if ($t -eq 'Automatic' -and $s.Status -ne 'Running') { Start-Service -Name $n -ErrorAction SilentlyContinue }
    } catch {}
  }
}
"""
        if is_admin():
            r = run_ps(script)
            ok = (r.returncode == 0)
            return ok, "Restored default service startup types." if ok else (r.stderr or r.stdout or "Failed to restore defaults.")
        else:
            ok = run_ps_elevated_blocking(script)
            return ok, "Restored default service startup types (elevated)." if ok else "Failed (UAC denied)."
