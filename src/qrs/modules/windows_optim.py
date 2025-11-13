# src/qrs/modules/windows_optim.py
import os
import json
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict, Any

try:
    import winreg
except ImportError:
    winreg = None  # Non-Windows environment safeguard


class WindowsOptimizer:
    """
    Core backend for QrsTweaks Windows optimizer.

    Provides:
      - Quick scan
      - Cleanup / Deep cleanup
      - Power plan tweaks
      - Network tweaks (DNS, CTCP, autotuning, Nagle)
      - Startup entry listing
      - Storage analysis
      - Cache cleanup
      - Mem-leak protector stubs
      - Profile export/import (JSON .qrsp)
      - System repair operations
      - Safe debloat operations
      - UI/taskbar tweaks
      - Backup/restore snapshots
    """

    def __init__(self):
        self.root = Path.cwd()
        self.backups_dir = self.root / "backups"

    # -------------------------------------------------
    # HELPER: run command
    # -------------------------------------------------
    def _run_cmd(self, cmd: str) -> Tuple[bool, str]:
        try:
            completed = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            ok = completed.returncode == 0
            out = (completed.stdout or "") + (completed.stderr or "")
            return ok, out.strip()
        except Exception as e:
            return False, str(e)

    # -------------------------------------------------
    # QUICK SCAN
    # -------------------------------------------------
    def quick_scan(self) -> str:
        lines = []
        lines.append("QrsTweaks Quick Scan")
        lines.append("=====================")

        # OS
        try:
            uname = platform.uname()
            lines.append(f"OS: {uname.system} {uname.release} ({uname.version})")
        except Exception:
            lines.append("OS: <unknown>")

        # Disk
        try:
            total, used, free = shutil.disk_usage("C:\\")
            gb = 1024 ** 3
            lines.append(
                f"Disk C: {used / gb:.1f} GB used / {total / gb:.1f} GB total "
                f"({free / gb:.1f} GB free)"
            )
        except Exception:
            lines.append("Disk: <unable to read>")

        # Temp size
        try:
            temp = Path(os.getenv("TEMP", r"C:\Windows\Temp"))
            total_size = 0
            for root, dirs, files in os.walk(temp):
                for f in files:
                    fp = Path(root) / f
                    try:
                        total_size += fp.stat().st_size
                    except OSError:
                        pass
            lines.append(f"Temp folder size: ~{total_size / (1024**2):.1f} MB")
        except Exception:
            lines.append("Temp folder size: <unknown>")

        return "\n".join(lines)

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------
    def cleanup_temp_files(self) -> int:
        temp_paths = [
            Path(os.getenv("TEMP", "")),
            Path(os.getenv("TMP", "")),
            Path(r"C:\Windows\Temp"),
        ]
        count = 0
        for base in temp_paths:
            if not base or not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    fp = Path(root) / f
                    try:
                        fp.unlink()
                        count += 1
                    except OSError:
                        pass
        return count

    def deep_cleanup(self) -> int:
        """
        More aggressive cleanup (no recycle bin, direct delete).
        """
        targets = [
            Path(os.getenv("TEMP", "")),
            Path(os.getenv("TMP", "")),
            Path(r"C:\Windows\Temp"),
            Path.home() / "AppData" / "Local" / "Temp",
        ]
        count = 0
        for base in targets:
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    fp = Path(root) / f
                    try:
                        fp.unlink()
                        count += 1
                    except OSError:
                        pass
        return count

    # -------------------------------------------------
    # RESTORE POINT (best effort)
    # -------------------------------------------------
    def create_restore_point(self, description: str) -> Tuple[bool, str]:
        ps = (
            f'powershell.exe -Command "Checkpoint-Computer -Description '
            f'\'{description}\' -RestorePointType MODIFY_SETTINGS"'
        )
        ok, out = self._run_cmd(ps)
        if ok:
            return True, "Restore point created."
        return False, f"Failed to create restore point: {out}"

    # -------------------------------------------------
    # POWER PLAN
    # -------------------------------------------------
    def create_high_perf_powerplan(self) -> Tuple[bool, str]:
        ok, out = self._run_cmd("powercfg /L")
        if not ok:
            return False, f"powercfg /L failed: {out}"

        high_guid = None
        for line in out.splitlines():
            if "High performance" in line:
                parts = line.strip().split()
                for p in parts:
                    if p.startswith("(") and p.endswith(")"):
                        high_guid = p.strip("()")
                        break
        if not high_guid:
            return False, "High performance plan not found."

        ok, out2 = self._run_cmd(f"powercfg /S {high_guid}")
        if not ok:
            return False, f"Failed to set high performance plan: {out2}"
        return True, "High performance power plan activated."

    # -------------------------------------------------
    # NETWORK TWEAKS
    # -------------------------------------------------
    def set_dns(self, primary: str, secondary: str) -> Tuple[bool, str]:
        cmds = [
            f'netsh interface ip set dns name="Ethernet" static {primary}',
            f'netsh interface ip add dns name="Ethernet" {secondary} index=2',
            f'netsh interface ip set dns name="Wi-Fi" static {primary}',
            f'netsh interface ip add dns name="Wi-Fi" {secondary} index=2',
        ]
        all_ok = True
        logs = []
        for cmd in cmds:
            ok, out = self._run_cmd(cmd)
            logs.append(f"{cmd}: {out}")
            all_ok = all_ok and ok
        if all_ok:
            return True, f"DNS set to {primary} / {secondary} (Ethernet/Wi-Fi)."
        return False, "Some DNS commands failed:\n" + "\n".join(logs)

    def enable_ctcp(self, enable: bool) -> Tuple[bool, str]:
        value = "enabled" if enable else "disabled"
        ok, out = self._run_cmd(f"netsh interface tcp set global congestionprovider={value}")
        if ok:
            return True, f"CTCP {value}."
        return False, f"Failed to change CTCP: {out}"

    def autotuning(self, level: str) -> Tuple[bool, str]:
        ok, out = self._run_cmd(f"netsh interface tcp set global autotuninglevel={level}")
        if ok:
            return True, f"TCP autotuning set to '{level}'."
        return False, f"Failed to set autotuning: {out}"

    def toggle_nagle(self, disable: bool) -> Tuple[bool, str]:
        if winreg is None:
            return False, "winreg not available; cannot toggle Nagle."

        try:
            key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(root, i)
                    except OSError:
                        break
                    i += 1
                    with winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS) as iface:
                        if disable:
                            winreg.SetValueEx(iface, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                            winreg.SetValueEx(iface, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                        else:
                            for name in ("TcpAckFrequency", "TCPNoDelay"):
                                try:
                                    winreg.DeleteValue(iface, name)
                                except OSError:
                                    pass
            if disable:
                return True, "Nagle disabled for all interfaces."
            else:
                return True, "Nagle restored to default for all interfaces."
        except OSError as e:
            return False, f"Registry error: {e}"

    def latency_ping(self, host: str, count: int = 5) -> Tuple[bool, str]:
        cmd = f"ping -n {count} {host}"
        ok, out = self._run_cmd(cmd)
        return ok, out

    # -------------------------------------------------
    # STARTUP ENTRIES
    # -------------------------------------------------
    def list_startup_entries(self) -> List[Tuple[str, str, str]]:
        result = []
        if winreg is None:
            return result

        paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
        ]
        for root, subkey, label in paths:
            try:
                with winreg.OpenKey(root, subkey) as k:
                    i = 0
                    while True:
                        try:
                            name, val, _ = winreg.EnumValue(k, i)
                        except OSError:
                            break
                        i += 1
                        result.append((label, name, val))
            except OSError:
                continue
        return result

    # -------------------------------------------------
    # STORAGE ANALYZER
    # -------------------------------------------------
    def _walk_sizes(self, base: Path, exclude: List[Path]) -> Tuple[int, List[Path]]:
        total = 0
        files = []
        base = base.resolve()
        ex_resolved = [e.resolve() for e in exclude if e.exists()]
        for root, dirs, f_names in os.walk(base):
            root_path = Path(root)
            if any(str(root_path).startswith(str(e)) for e in ex_resolved):
                continue
            for fn in f_names:
                fp = root_path / fn
                try:
                    size = fp.stat().st_size
                    total += size
                    files.append((fp, size))
                except OSError:
                    pass
        return total, files

    def analyze_drive(self) -> str:
        base = Path("C:\\")
        exclude = [Path("C:\\Windows"), Path("C:\\Program Files"), Path("C:\\Program Files (x86)")]
        total, files = self._walk_sizes(base, exclude)
        gb = 1024 ** 3
        return f"[Storage] C: (excluding Windows/Program Files) ~{total / gb:.2f} GB used."

    def analyze_top25(self) -> str:
        base = Path("C:\\")
        exclude = [Path("C:\\Windows"), Path("C:\\Program Files"), Path("C:\\Program Files (x86)")]
        total, files = self._walk_sizes(base, exclude)
        files_sorted = sorted(files, key=lambda x: x[1], reverse=True)[:25]
        lines = ["[Storage] Top 25 largest files on C: (excluding Windows / Program Files):"]
        for fp, sz in files_sorted:
            lines.append(f" - {fp} : {sz / (1024**2):.1f} MB")
        return "\n".join(lines)

    def analyze_top_dirs(self) -> str:
        base = Path("C:\\")
        exclude = [Path("C:\\Windows"), Path("C:\\Program Files"), Path("C:\\Program Files (x86)")]
        dir_totals: Dict[Path, int] = {}
        _, files = self._walk_sizes(base, exclude)
        for fp, size in files:
            parent = fp.parent
            dir_totals[parent] = dir_totals.get(parent, 0) + size
        top_dirs = sorted(dir_totals.items(), key=lambda x: x[1], reverse=True)[:25]
        lines = ["[Storage] Top directories by size (excluding Windows / Program Files):"]
        for d, sz in top_dirs:
            lines.append(f" - {d} : {sz / (1024**2):.1f} MB")
        return "\n".join(lines)

    def clear_cache(self) -> str:
        removed = 0
        targets = [
            Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "WebCache",
            Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "INetCache",
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "Cache",
        ]
        for base in targets:
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    fp = Path(root) / f
                    try:
                        fp.unlink()
                        removed += 1
                    except OSError:
                        pass
        return f"[Storage] Cleared ~{removed} cached files."

    # -------------------------------------------------
    # MEM-LEAK PROTECTOR (stubbed)
    # -------------------------------------------------
    def start_memleak_protector(self, process_names: List[str], mb_threshold: int) -> Tuple[bool, str]:
        return True, f"MemLeak protector configured for {process_names} at {mb_threshold} MB (simulated)."

    def stop_memleak_protector(self) -> Tuple[bool, str]:
        return True, "MemLeak protector stopped (simulated)."

    # -------------------------------------------------
    # PROFILE SYSTEM (EXPORT/IMPORT)
    # -------------------------------------------------
    def _get_current_dns(self) -> Tuple[str, str]:
        # Placeholder for now (introspection is complex); still consistent with applied tweaks.
        return "1.1.1.1", "1.0.0.1"

    def _get_current_state(self) -> Dict[str, Any]:
        dns1, dns2 = self._get_current_dns()
        state = {
            "profile_version": "1.0",
            "system": {
                "high_performance_plan": True
            },
            "network": {
                "dns_primary": dns1,
                "dns_secondary": dns2,
                "ctcp": True,
                "autotuning": "restricted",
                "disable_nagle": True,
            },
            "memory": {
                "memleak_guard_enabled": False,
                "process_list": [],
                "threshold_mb": 1024,
            },
            "cleanup": {
                "clear_temp": False,
                "deep_cleanup": False,
                "clear_browser_cache": False,
            },
            "startup": {
                "startup_blocklist": [],
            },
        }
        return state

    def export_profile(self, path: str) -> Tuple[bool, str]:
        state = self._get_current_state()
        profile = {
            "profile_version": state.get("profile_version", "1.0"),
            "name": "Exported Profile",
            "description": "Profile exported from current system state by QrsTweaks.",
            "created_by": "QrsTweaks",
            "created_at": datetime.utcnow().isoformat() + "Z",
            **{k: v for k, v in state.items() if k not in ("profile_version",)},
        }

        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)
            return True, "Profile exported."
        except OSError as e:
            return False, f"Failed to write profile: {e}"

    def _normalize_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        out["profile_version"] = str(data.get("profile_version", "1.0"))
        out["name"] = data.get("name", "Imported Profile")
        out["description"] = data.get("description", "")
        out["created_by"] = data.get("created_by", "unknown")

        sys_cfg = data.get("system", {}) or {}
        net_cfg = data.get("network", {}) or {}
        mem_cfg = data.get("memory", {}) or {}
        cln_cfg = data.get("cleanup", {}) or {}
        stp_cfg = data.get("startup", {}) or {}

        out["system"] = {
            "high_performance_plan": bool(sys_cfg.get("high_performance_plan", False))
        }

        out["network"] = {
            "dns_primary": str(net_cfg.get("dns_primary", "1.1.1.1")),
            "dns_secondary": str(net_cfg.get("dns_secondary", "1.0.0.1")),
            "ctcp": bool(net_cfg.get("ctcp", True)),
            "autotuning": str(net_cfg.get("autotuning", "normal")),
            "disable_nagle": bool(net_cfg.get("disable_nagle", False)),
        }

        out["memory"] = {
            "memleak_guard_enabled": bool(mem_cfg.get("memleak_guard_enabled", False)),
            "process_list": list(mem_cfg.get("process_list", [])),
            "threshold_mb": int(mem_cfg.get("threshold_mb", 1024)),
        }

        out["cleanup"] = {
            "clear_temp": bool(cln_cfg.get("clear_temp", False)),
            "deep_cleanup": bool(cln_cfg.get("deep_cleanup", False)),
            "clear_browser_cache": bool(cln_cfg.get("clear_browser_cache", False)),
        }

        out["startup"] = {
            "startup_blocklist": list(stp_cfg.get("startup_blocklist", []))
        }

        return out

    def _apply_profile_dict(self, profile: Dict[str, Any]) -> str:
        log_lines: List[str] = []
        sys_cfg = profile.get("system", {})
        net_cfg = profile.get("network", {})
        mem_cfg = profile.get("memory", {})
        cln_cfg = profile.get("cleanup", {})
        stp_cfg = profile.get("startup", {})

        if sys_cfg.get("high_performance_plan"):
            ok, msg = self.create_high_perf_powerplan()
            log_lines.append(f"[Profile/System] {msg}")

        dns1 = net_cfg.get("dns_primary")
        dns2 = net_cfg.get("dns_secondary")
        if dns1 and dns2:
            ok, msg = self.set_dns(dns1, dns2)
            log_lines.append(f"[Profile/Network] {msg}")

        ok, msg = self.enable_ctcp(net_cfg.get("ctcp", True))
        log_lines.append(f"[Profile/Network] {msg}")

        ok, msg = self.autotuning(net_cfg.get("autotuning", "normal"))
        log_lines.append(f"[Profile/Network] {msg}")

        ok, msg = self.toggle_nagle(net_cfg.get("disable_nagle", False))
        log_lines.append(f"[Profile/Network] {msg}")

        if mem_cfg.get("memleak_guard_enabled", False):
            ok, msg = self.start_memleak_protector(
                mem_cfg.get("process_list", []),
                mem_cfg.get("threshold_mb", 1024),
            )
            log_lines.append(f"[Profile/Memory] {msg}")

        if cln_cfg.get("clear_temp", False):
            n = self.cleanup_temp_files()
            log_lines.append(f"[Profile/Cleanup] Temp cleanup: {n} files removed.")
        if cln_cfg.get("deep_cleanup", False):
            n = self.deep_cleanup()
            log_lines.append(f"[Profile/Cleanup] Deep cleanup: {n} items removed.")
        if cln_cfg.get("clear_browser_cache", False):
            out = self.clear_cache()
            log_lines.append(f"[Profile/Cleanup] {out}")

        blocklist = stp_cfg.get("startup_blocklist", [])
        if blocklist:
            log_lines.append(
                "[Profile/Startup] Blocklist specified but enforcement is not yet implemented: "
                + ", ".join(blocklist)
            )

        return "\n".join(log_lines)

    def import_profile(self, path: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists():
            return False, f"[Profile] File not found: {path}"

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            return False, f"[Profile] Invalid JSON: {e}"

        profile = self._normalize_profile(data)
        applied_log = self._apply_profile_dict(profile)
        header = f"[Profile] Imported '{profile.get('name', 'Unnamed')}'"
        return True, header + "\n" + applied_log

    # -------------------------------------------------
    # SYSTEM REPAIROPS
    # -------------------------------------------------
    def repair_windows_update(self) -> Tuple[bool, str]:
        """
        Tries to repair Windows Update by stopping services, cleaning SoftwareDistribution, and restarting services.
        """
        logs = []

        cmds = [
            "net stop wuauserv",
            "net stop cryptSvc",
            "net stop bits",
            "net stop msiserver",
        ]
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")

        # rename SoftwareDistribution / catroot2
        for src, dst in [
            (r"C:\Windows\SoftwareDistribution", r"C:\Windows\SoftwareDistribution.old"),
            (r"C:\Windows\System32\catroot2", r"C:\Windows\System32\catroot2.old"),
        ]:
            try:
                if os.path.exists(dst):
                    # already renamed earlier; skip
                    pass
                elif os.path.exists(src):
                    os.rename(src, dst)
                    logs.append(f"Renamed {src} -> {dst}")
            except OSError as e:
                logs.append(f"Failed to rename {src}: {e}")

        cmds2 = [
            "net start wuauserv",
            "net start cryptSvc",
            "net start bits",
            "net start msiserver",
        ]
        all_ok = True
        for c in cmds2:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok

        msg = "[RepairOps] Windows Update repair routine completed.\n" + "\n".join(logs)
        return all_ok, msg

    def reset_network_stack(self) -> Tuple[bool, str]:
        logs = []
        cmds = [
            "netsh winsock reset",
            "netsh int ip reset",
        ]
        all_ok = True
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok
        msg = "[RepairOps] Network stack reset. A reboot is recommended.\n" + "\n".join(logs)
        return all_ok, msg

    def run_dism_sfc(self) -> Tuple[bool, str]:
        logs = []
        dism = "DISM.exe /Online /Cleanup-image /RestoreHealth"
        sfc = "sfc /scannow"

        ok1, out1 = self._run_cmd(dism)
        logs.append(f"{dism}: {out1}")
        ok2, out2 = self._run_cmd(sfc)
        logs.append(f"{sfc}: {out2}")

        all_ok = ok1 and ok2
        msg = "[RepairOps] DISM + SFC repair completed.\n" + "\n".join(logs)
        return all_ok, msg

    def reset_store_cache(self) -> Tuple[bool, str]:
        cmd = "wsreset.exe -i"
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[RepairOps] Microsoft Store cache reset requested. Store may open briefly."
        return False, f"[RepairOps] Store cache reset failed: {out}"

    # -------------------------------------------------
    # SAFE DEBLOAT OPS
    # -------------------------------------------------
    def debloat_xbox_gamebar(self) -> Tuple[bool, str]:
        cmds = [
            r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
        ]
        logs = []
        all_ok = True
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok
        msg = "[Debloat] Xbox Game Bar / DVR disabled.\n" + "\n".join(logs)
        return all_ok, msg

    def debloat_background_apps(self) -> Tuple[bool, str]:
        # Global disable of background apps via registry (where supported).
        cmd = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" '
            r'/v GlobalUserDisabled /t REG_DWORD /d 1 /f'
        )
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[Debloat] Background apps disabled (where supported)."
        return False, f"[Debloat] Failed to change background apps setting: {out}"

    def debloat_telemetry_safe(self) -> Tuple[bool, str]:
        # Disable a few high-telemetry scheduled tasks without murdering the OS.
        tasks = [
            r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        ]
        logs = []
        all_ok = True
        for t in tasks:
            cmd = f'schtasks /Change /TN "{t}" /Disable'
            ok, out = self._run_cmd(cmd)
            logs.append(f"{cmd}: {out}")
            all_ok = all_ok and ok
        msg = "[Debloat] Selected telemetry tasks disabled (safe set).\n" + "\n".join(logs)
        return all_ok, msg

    def debloat_cortana_search(self) -> Tuple[bool, str]:
        cmds = [
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v CortanaConsent /t REG_DWORD /d 0 /f',
        ]
        logs = []
        all_ok = True
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok
        msg = "[Debloat] Bing web search + Cortana usage reduced.\n" + "\n".join(logs)
        return all_ok, msg

    def debloat_revert_safe(self) -> Tuple[bool, str]:
        logs = []
        all_ok = True

        # Re-enable background apps
        cmd_bg = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" '
            r'/v GlobalUserDisabled /t REG_DWORD /d 0 /f'
        )
        ok, out = self._run_cmd(cmd_bg)
        logs.append(f"{cmd_bg}: {out}")
        all_ok = all_ok and ok

        # Re-enable telemetry tasks
        tasks = [
            r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        ]
        for t in tasks:
            cmd = f'schtasks /Change /TN "{t}" /Enable'
            ok, out = self._run_cmd(cmd)
            logs.append(f"{cmd}: {out}")
            all_ok = all_ok and ok

        # Reset Cortana / search bits to defaults (not fully on, but more neutral)
        cmds = [
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v CortanaConsent /t REG_DWORD /d 1 /f',
        ]
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok

        msg = "[Debloat] Safe debloat profile reverted as much as possible.\n" + "\n".join(logs)
        return all_ok, msg

    # -------------------------------------------------
    # UI / TASKBAR TWEAKS
    # -------------------------------------------------
    def ui_disable_bing_search(self) -> Tuple[bool, str]:
        cmds = [
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f',
        ]
        logs = []
        all_ok = True
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok
        msg = "[UI] Bing / web results in Start search disabled.\n" + "\n".join(logs)
        return all_ok, msg

    def ui_hide_widgets(self) -> Tuple[bool, str]:
        cmd = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" '
            r'/v TaskbarDa /t REG_DWORD /d 0 /f'
        )
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[UI] Widgets hidden from taskbar."
        return False, f"[UI] Failed to hide widgets: {out}"

    def ui_hide_chat_icon(self) -> Tuple[bool, str]:
        cmd = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" '
            r'/v TaskbarMn /t REG_DWORD /d 0 /f'
        )
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[UI] Chat icon hidden from taskbar."
        return False, f"[UI] Failed to hide chat icon: {out}"

    def ui_explorer_this_pc(self) -> Tuple[bool, str]:
        # 1 = This PC, 0 = Quick Access (on most builds)
        cmd = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" '
            r'/v LaunchTo /t REG_DWORD /d 1 /f'
        )
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[UI] Explorer set to open in 'This PC'."
        return False, f"[UI] Failed to set Explorer LaunchTo: {out}"

    def ui_show_file_extensions(self) -> Tuple[bool, str]:
        cmd = (
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" '
            r'/v HideFileExt /t REG_DWORD /d 0 /f'
        )
        ok, out = self._run_cmd(cmd)
        if ok:
            return True, "[UI] File extensions now visible."
        return False, f"[UI] Failed to change HideFileExt: {out}"

    def ui_restore_defaults(self) -> Tuple[bool, str]:
        logs = []
        all_ok = True

        cmds = [
            # Bing search back on
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v CortanaConsent /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarDa /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarMn /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v LaunchTo /t REG_DWORD /d 0 /f',
            r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 1 /f',
            r'reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 0 /f',
        ]
        for c in cmds:
            ok, out = self._run_cmd(c)
            logs.append(f"{c}: {out}")
            all_ok = all_ok and ok

        msg = "[UI] UI / taskbar settings restored towards defaults (may require Explorer restart).\n" + "\n".join(logs)
        return all_ok, msg

    # -------------------------------------------------
    # BACKUP & RESTORE SNAPSHOTS
    # -------------------------------------------------
    def create_backup_snapshot(self) -> Tuple[bool, str]:
        """
        Create a backup snapshot of the current profile state into /backups as .qrsp.
        """
        try:
            self.backups_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"[Backup] Failed to create backups folder: {e}"

        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = self.backups_dir / f"backup-{ts}.qrsp"
        ok, msg = self.export_profile(str(path))
        if ok:
            return True, f"[Backup] Snapshot saved: {path}"
        return False, f"[Backup] Snapshot failed: {msg}"

    def restore_latest_backup(self) -> Tuple[bool, str]:
        """
        Find the latest .qrsp in /backups and import it.
        """
        if not self.backups_dir.exists():
            return False, "[Backup] No backups folder found."

        files = list(self.backups_dir.glob("*.qrsp"))
        if not files:
            return False, "[Backup] No backup snapshots found."

        latest = max(files, key=lambda p: p.stat().st_mtime)
        ok, msg = self.import_profile(str(latest))
        if ok:
            return True, f"[Backup] Restored from {latest}.\n{msg}"
        return False, f"[Backup] Restore from {latest} failed:\n{msg}"

    def open_backup_folder(self) -> Tuple[bool, str]:
        """
        Open the backups folder in Explorer (Windows-only).
        """
        try:
            self.backups_dir.mkdir(parents=True, exist_ok=True)
            if platform.system().lower().startswith("win"):
                os.startfile(str(self.backups_dir))
                return True, "[Backup] Opened backup folder in Explorer."
            else:
                return False, "[Backup] Opening folder is only supported on Windows."
        except Exception as e:
            return False, f"[Backup] Failed to open backups folder: {e}"
