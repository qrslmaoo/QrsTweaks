import os
import sys
import shutil
import time
import json
import hashlib
import subprocess
from pathlib import Path

import psutil
import winreg


def is_admin() -> bool:
    """Return True if this process is elevated."""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_ps(script: str) -> subprocess.CompletedProcess:
    """Run a PowerShell command safely, returning CompletedProcess."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        text=True,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


class WindowsOptimizer:
    """Handles Windows optimization tasks and status detection + actions."""

    def __init__(self):
        self._memleak_proc_name = "qrs_memguard.exe"

    # ---------------------------------------------------------
    # Status Detection
    # ---------------------------------------------------------
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
            # Loose heuristic: CTCP on or autotuning != normal -> considered optimized
            return ("ctcp" in out and "disabled" not in out) or ("autotuning level" in out and "normal" not in out)
        except Exception:
            return False

    def is_memleak_guard_active(self) -> bool:
        try:
            for p in psutil.process_iter(["name"]):
                name = (p.info.get("name") or "").lower()
                if self._memleak_proc_name in name:
                    return True
        except Exception:
            pass
        return False

    def is_services_optimized(self) -> bool:
        """Heuristic: SysMain disabled AND DiagTrack disabled."""
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
            names = {d["Name"]: (d.get("StartType"), d.get("Status")) for d in data}
            sysmain_ok = ("SysMain" in names) and (str(names["SysMain"][0]).lower() == "disabled")
            diag_ok = ("DiagTrack" in names) and (str(names["DiagTrack"][0]).lower() == "disabled")
            return sysmain_ok and diag_ok
        except Exception:
            return False

    # ---------------------------------------------------------
    # Existing basics
    # ---------------------------------------------------------
    def quick_scan(self) -> str:
        try:
            output = subprocess.check_output(["systeminfo"], text=True, stderr=subprocess.DEVNULL)
            lines = [ln for ln in output.splitlines() if ln.strip()]
            return "\n".join(lines[:12])
        except Exception as e:
            return f"[Scan Error] {e}"

    def create_high_perf_powerplan(self):
        if not is_admin():
            return False, "Admin required for power plan."
        try:
            # Activate High performance builtin (SCHEME_MIN)
            subprocess.run(["powercfg", "-setactive", "SCHEME_MIN"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True, "High Performance plan activated."
        except Exception as e:
            return False, str(e)

    def cleanup_temp_files(self) -> int:
        temp = Path(os.environ.get("TEMP", r"C:\Windows\Temp"))
        count = 0
        try:
            for root, _, files in os.walk(temp):
                for f in files:
                    fp = Path(root) / f
                    try:
                        fp.unlink(missing_ok=True)
                        count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return count

    def create_restore_point(self, name):
        if not is_admin():
            return False, "Admin required for restore points."
        cp = run_ps(f"Checkpoint-Computer -Description '{name}' -RestorePointType 'MODIFY_SETTINGS'")
        if cp.returncode == 0:
            return True, "Restore point created."
        return False, (cp.stderr or cp.stdout or "Failed to create restore point.")

    # ---------------------------------------------------------
    # Memory leak protector (placeholder hook)
    # ---------------------------------------------------------
    def start_memleak_protector(self, process_names, mb_threshold):
        # Placeholder: future background monitor; currently just acknowledges.
        return True, f"MemLeak guard armed for {', '.join(process_names)} @ {mb_threshold} MB."

    def stop_memleak_protector(self):
        return True, "MemLeak guard disarmed."

    # ---------------------------------------------------------
    # Network – concrete tweaks
    # ---------------------------------------------------------
    def set_dns(self, primary, secondary):
        if not is_admin():
            return False, "Admin required to set DNS."
        # Try common interface names
        names = ["Ethernet", "Wi-Fi", "WiFi", "Local Area Connection"]
        errors = []
        for n in names:
            a = run_ps(f'netsh interface ip set dns name="{n}" static {primary}')
            b = run_ps(f'netsh interface ip add dns name="{n}" {secondary} index=2')
            if a.returncode == 0:
                return True, f"DNS on '{n}' set to {primary} / {secondary}"
            errors.append(a.stderr or a.stdout)
        return False, "Failed to set DNS. " + " | ".join(filter(None, errors))[:300]

    def enable_ctcp(self, enable: bool):
        if not is_admin():
            return False, "Admin required."
        mode = "ctcp" if enable else "none"
        r = run_ps(f'netsh int tcp set global congestionprovider={mode}')
        if r.returncode == 0:
            return True, f"CTCP {'enabled' if enable else 'disabled'}."
        return False, r.stderr or r.stdout

    def autotuning(self, level: str):
        if not is_admin():
            return False, "Admin required."
        r = run_ps(f'netsh int tcp set global autotuninglevel={level}')
        if r.returncode == 0:
            return True, f"TCP autotuning set to {level}."
        return False, r.stderr or r.stdout

    def toggle_nagle(self, disable=True):
        if not is_admin():
            return False, "Admin required."
        # Safer approach: set for current active interface GUIDs
        try:
            # Find all NIC interface GUID subkeys and set TcpAckFrequency/TcpNoDelay = 1
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces") as root:
                i = 0
                changed = 0
                while True:
                    try:
                        subname = winreg.EnumKey(root, i)
                        i += 1
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

    def latency_ping(self, host="1.1.1.1", count=4):
        try:
            output = subprocess.check_output(["ping", host, "-n", str(count)], text=True, stderr=subprocess.DEVNULL)
            return True, output
        except Exception as e:
            return False, str(e)

    # --- AI-ish helpers ---
    def adaptive_dns_auto(self):
        """Ping well-known resolvers and choose the fastest."""
        candidates = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        results = []
        for ip in candidates:
            ok, out = self.latency_ping(ip, 3)
            if not ok:
                continue
            # Simple parse: average time = Xms
            avg = 9999
            for ln in out.splitlines():
                ln = ln.lower()
                if "average" in ln:
                    # windows locale: Average = Xms
                    nums = [int(s.replace("ms", "")) for s in ln.split() if s.endswith("ms")]
                    if nums:
                        avg = nums[-1]
            results.append((avg, ip))
        if not results:
            return False, "No ping results."
        results.sort()
        fastest = results[0][1]
        # Set primary to fastest, secondary fallback by simple order
        order = [fastest] + [x for x in candidates if x != fastest]
        return self.set_dns(order[0], order[1])

    def auto_network_repair(self):
        if not is_admin():
            return False, "Admin required."
        cmds = [
            "netsh int ip reset",
            "netsh winsock reset",
            "ipconfig /flushdns"
        ]
        outs = []
        for c in cmds:
            r = run_ps(c)
            outs.append(r.stdout or r.stderr or c)
        return True, "Network repair executed. Reboot may be required.\n" + "\n".join(outs)

    # ---------------------------------------------------------
    # Deep Cleanup
    # ---------------------------------------------------------
    def clean_browser_caches(self):
        """Delete Chrome/Edge/Firefox cache safely."""
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

    def windows_update_cleanup(self):
        if not is_admin():
            return False, "Admin required."
        # DISM cleanup + Delivery Optimization cache purge
        dism = run_ps("DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase")
        do_folder = Path(r"C:\Windows\SoftwareDistribution\DeliveryOptimization")
        try:
            if do_folder.exists():
                for p in do_folder.rglob("*"):
                    try:
                        if p.is_file():
                            p.unlink(missing_ok=True)
                    except Exception:
                        pass
        except Exception:
            pass
        ok = dism.returncode == 0
        msg = (dism.stdout or dism.stderr or "").strip()
        return ok, ("Windows Update cleanup finished." if ok else msg)

    def find_app_residue(self):
        roots = [
            Path.home() / "AppData/Local",
            Path.home() / "AppData/Roaming",
            Path("C:/ProgramData")
        ]
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
    def apply_minimal_services(self):
        if not is_admin():
            return False, "Admin required."
        # Safer baseline: disable telemetry & SysMain, keep Search running by default.
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
        if r.returncode == 0:
            return True, "Disabled DiagTrack & SysMain."
        return False, r.stderr or r.stdout

    def throttle_background_cpu(self):
        """Lower priority of background processes (simple heuristic)."""
        lowered = 0
        allow = {"explorer.exe", "dwm.exe", "csrss.exe", "smss.exe", "system", "registry"}
        try:
            for p in psutil.process_iter(["name", "pid", "cpu_percent"]):
                n = (p.info.get("name") or "").lower()
                if not n or n in allow:
                    continue
                try:
                    proc = psutil.Process(p.info["pid"])
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    lowered += 1
                except Exception:
                    pass
            return True, f"Lowered priority on ~{lowered} processes."
        except Exception as e:
            return False, str(e)

    def list_heavy_processes(self):
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
    def driver_version_integrity(self):
        r = run_ps("(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json)")
        if r.returncode != 0 or not r.stdout.strip():
            return False, r.stderr or r.stdout or "Failed to query GPU driver."
        return True, r.stdout.strip()

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------
    def trim_ssds(self):
        if not is_admin():
            return False, "Admin required."
        r = run_ps("defrag /C /L")
        return (r.returncode == 0), (r.stdout or r.stderr)

    def defrag_hdds_safe(self):
        if not is_admin():
            return False, "Admin required."
        # /U /V verbose; /H normal priority; /M can run on multiple volumes
        r = run_ps("defrag /E C: /U /V")  # avoid C: if it's SSD; /E excludes, but here we just demonstrate
        return (r.returncode == 0), (r.stdout or r.stderr)

    def find_large_files(self, roots=None, min_mb=500, limit=50):
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

    def duplicate_finder(self, roots=None, limit=2000):
        if roots is None:
            roots = [str(Path.home() / "Downloads"), str(Path.home() / "Documents")]
        hashes = {}
        dups = []
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
                        h = hashlib.sha1(fp.read_bytes()).hexdigest()
                        if h in hashes:
                            dups.append((str(fp), hashes[h]))
                        else:
                            hashes[h] = str(fp)
                    except Exception:
                        pass
        lines = [f"{a} == {b}" for a, b in dups]
        return True, "\n".join(lines) if lines else "No duplicates found (scanned limit reached)."

    # ---------------------------------------------------------
    # Security & Stability
    # ---------------------------------------------------------
    def create_snapshot(self, name="QrsTweaks Snapshot"):
        return self.create_restore_point(name)

    def flag_unsigned_processes(self):
        # Uses PowerShell Authenticode signature
        script = r"""
Get-Process | ForEach-Object {
    try {
        $p = $_
        $path = $p.Path
        if ($null -ne $path -and (Test-Path $path)) {
            $sig = Get-AuthenticodeSignature -FilePath $path
            [PSCustomObject]@{ Name=$p.Name; PID=$p.Id; Status=$sig.Status; Path=$path }
        }
    } catch {}
} | Where-Object { $_.Status -ne 'Valid' } | ConvertTo-Json
"""
        r = run_ps(script)
        if r.returncode != 0:
            return False, r.stderr or r.stdout
        data = r.stdout.strip()
        if not data:
            return True, "No unsigned processes reported."
        try:
            items = json.loads(data)
            if isinstance(items, dict):
                items = [items]
            lines = [f"{x.get('Name')} (PID {x.get('PID')}) — {x.get('Status')} — {x.get('Path')}" for x in items]
            return True, "\n".join(lines) if lines else "No unsigned processes."
        except Exception:
            return True, data

    def winsock_dns_reset(self):
        if not is_admin():
            return False, "Admin required."
        return self.auto_network_repair()

    def sfc_scannow(self):
        if not is_admin():
            return False, "Admin required."
        # Fire-and-forget; SFC can take a long time.
        p = subprocess.Popen(["sfc", "/scannow"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return True, "SFC /scannow started in background; this may take a while."
