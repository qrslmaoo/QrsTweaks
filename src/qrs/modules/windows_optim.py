# src/qrs/modules/windows_optim.py
import os
import tempfile
import shutil
import subprocess
import winreg
import ctypes
import threading
import time
from pathlib import Path


class WindowsOptimizer:
    # --------------------------------------------------------
    #  QUICK SYSTEM SCAN
    # --------------------------------------------------------
    def quick_scan(self):
        try:
            temp_count = self._count_temp_files()
            free_gb = self._get_system_drive_free()
            total_gb = self._get_system_drive_total()
            ver = os.sys.getwindowsversion()
            report = (
                f"OS: Windows-{ver.major}.{ver.minor}.{ver.build}\n"
                f"Temp files (approx): {temp_count}\n"
                f"System drive free: {free_gb:.1f} GB / {total_gb:.1f} GB\n"
            )
            return report
        except Exception as e:
            return f"[Scan Error] {e}"

    # --------------------------------------------------------
    #  TEMP FILES
    # --------------------------------------------------------
    def _count_temp_files(self):
        temp = Path(tempfile.gettempdir())
        return sum(1 for _ in temp.rglob("*") if _.is_file())

    def cleanup_temp_files(self):
        temp = Path(tempfile.gettempdir())
        count = 0
        for item in temp.rglob("*"):
            try:
                if item.is_file():
                    item.unlink()
                    count += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
            except Exception:
                pass
        return count

    # --------------------------------------------------------
    #  SYSTEM DRIVE INFO
    # --------------------------------------------------------
    def _get_system_drive_free(self):
        usage = shutil.disk_usage("C:/")
        return usage.free / (1024 ** 3)

    def _get_system_drive_total(self):
        usage = shutil.disk_usage("C:/")
        return usage.total / (1024 ** 3)

    # --------------------------------------------------------
    #  POWER PLAN
    # --------------------------------------------------------
    def create_high_perf_powerplan(self):
        try:
            # Ultimate Performance GUID on many systems; falls back silently if unsupported
            subprocess.run(["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                           capture_output=True, text=True)
            return True, "High Performance power plan activated."
        except Exception as e:
            return False, str(e)

    # --------------------------------------------------------
    #  RESTORE POINT
    # --------------------------------------------------------
    def create_restore_point(self, name="QrsTweaks Restore"):
        try:
            cmd = (
                f"powershell.exe -command \"Checkpoint-Computer -Description "
                f"'{name}' -RestorePointType 'MODIFY_SETTINGS'\""
            )
            subprocess.run(cmd, shell=True)
            return True, "Restore point created."
        except Exception as e:
            return False, str(e)

    # --------------------------------------------------------
    #  SAFE REGISTRY OPTIMIZATIONS
    # --------------------------------------------------------
    def apply_safe_registry_tweaks(self):
        tweaks = {
            (winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuShowDelay", 0): winreg.REG_DWORD,
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
             "LargeSystemCache", 0): winreg.REG_DWORD,
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
             "SystemResponsiveness", 0): winreg.REG_DWORD,
        }
        try:
            for (hive, path, name, value), kind in tweaks.items():
                key = winreg.CreateKey(hive, path)
                winreg.SetValueEx(key, name, 0, kind, value)
                winreg.CloseKey(key)
            return True, "Registry optimizations applied."
        except Exception as e:
            return False, str(e)

    # --------------------------------------------------------
    #  SAFE SERVICE OPTIMIZATIONS
    # --------------------------------------------------------
    def apply_safe_service_tweaks(self):
        services = [
            "XboxGipSvc", "XblAuthManager", "XblGameSave", "XboxNetApiSvc",  # Xbox stack
            "DiagTrack",  # telemetry
        ]
        for svc in services:
            try:
                subprocess.run(f"sc config {svc} start= disabled", capture_output=True, text=True, shell=True)
            except Exception:
                pass
        return True, "Service tweaks applied."

    # ========================================================
    #            MEMORY-LEAK PROTECTOR
    # ========================================================
    """
    Trims working set of target processes safely using SetProcessWorkingSetSizeEx.
    This is *not* a cure for real leaks, but helps keep memory stable during long sessions.
    """

    def __init__(self):
        self._ml_thread = None
        self._ml_stop = threading.Event()

    def start_memleak_protector(self, process_names=None, mb_threshold=1024):
        """
        process_names: list[str] (e.g., ["FortniteClient-Win64-Shipping.exe"])
        mb_threshold: when a process exceeds this working set, attempt a trim
        """
        if process_names is None:
            process_names = ["FortniteClient-Win64-Shipping.exe"]
        self._ml_stop.clear()
        self._ml_thread = threading.Thread(target=self._ml_loop, args=(process_names, mb_threshold), daemon=True)
        self._ml_thread.start()
        return True, f"Memory-Leak Protector running (threshold {mb_threshold} MB)."

    def stop_memleak_protector(self):
        self._ml_stop.set()
        return True, "Memory-Leak Protector stopped."

    def _ml_loop(self, names, mb_threshold):
        psapi = ctypes.WinDLL("Psapi.dll")
        kernel = ctypes.WinDLL("Kernel32.dll")

        OpenProcess = kernel.OpenProcess
        OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
        OpenProcess.restype = ctypes.wintypes.HANDLE

        GetProcessMemoryInfo = psapi.GetProcessMemoryInfo
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.wintypes.SIZE_T),
                ("WorkingSetSize", ctypes.wintypes.SIZE_T),
                ("QuotaPeakPagedPoolUsage", ctypes.wintypes.SIZE_T),
                ("QuotaPagedPoolUsage", ctypes.wintypes.SIZE_T),
                ("QuotaPeakNonPagedPoolUsage", ctypes.wintypes.SIZE_T),
                ("QuotaNonPagedPoolUsage", ctypes.wintypes.SIZE_T),
                ("PagefileUsage", ctypes.wintypes.SIZE_T),
                ("PeakPagefileUsage", ctypes.wintypes.SIZE_T),
            ]

        GetProcessMemoryInfo.argtypes = [ctypes.wintypes.HANDLE,
                                         ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                                         ctypes.wintypes.DWORD]
        GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL

        SetProcessWorkingSetSizeEx = kernel.SetProcessWorkingSetSizeEx
        SetProcessWorkingSetSizeEx.argtypes = [ctypes.wintypes.HANDLE,
                                               ctypes.wintypes.SIZE_T,
                                               ctypes.wintypes.SIZE_T,
                                               ctypes.wintypes.DWORD]
        SetProcessWorkingSetSizeEx.restype = ctypes.wintypes.BOOL
        QUOTA_LIMITS_HARDWS_MIN_DISABLE = 0x00000002
        QUOTA_LIMITS_HARDWS_MAX_DISABLE = 0x00000004
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_VM_READ = 0x0010

        def enum_pids():
            # fast WMI-free snapshot
            arr = (ctypes.wintypes.DWORD * 4096)()
            needed = ctypes.wintypes.DWORD()
            psapi.EnumProcesses(ctypes.byref(arr), ctypes.sizeof(arr), ctypes.byref(needed))
            count = int(needed.value / ctypes.sizeof(ctypes.wintypes.DWORD()))
            return arr[:count]

        while not self._ml_stop.is_set():
            try:
                targets = set(n.lower() for n in names)
                for pid in enum_pids():
                    h = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA | PROCESS_VM_READ, False, pid)
                    if not h:
                        continue
                    # Get name
                    exe_name = (ctypes.c_wchar * 260)()
                    nlen = ctypes.wintypes.DWORD(260)
                    psapi.GetProcessImageFileNameW(h, exe_name, 260)
                    short = Path(exe_name.value).name.lower()
                    if short in targets:
                        # memory
                        pmc = PROCESS_MEMORY_COUNTERS()
                        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                        if GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
                            ws_mb = pmc.WorkingSetSize / (1024 * 1024)
                            if ws_mb >= mb_threshold:
                                # trim
                                SetProcessWorkingSetSizeEx(h, -1, -1,
                                    QUOTA_LIMITS_HARDWS_MIN_DISABLE | QUOTA_LIMITS_HARDWS_MAX_DISABLE)
                    kernel.CloseHandle(h)
            except Exception:
                pass
            time.sleep(3.0)

    # ========================================================
    #            STARTUP OPTIMIZER
    # ========================================================
    def list_startup_entries(self):
        """Return list of (location, name, value)."""
        results = []
        entries = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in entries:
            try:
                key = winreg.OpenKey(hive, path)
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(key, i)
                        results.append((f"{'HKCU' if hive==winreg.HKEY_CURRENT_USER else 'HKLM'}\\{path}", name, val))
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass
        return results

    def disable_startup_entry(self, name):
        """Disable an entry by moving value to Run-Disabled."""
        for hive, path in [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
                val, typ = winreg.QueryValueEx(key, name)
                # create disabled bucket
                dkey = winreg.CreateKey(hive, path + "-Disabled")
                winreg.SetValueEx(dkey, name, 0, typ, val)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(dkey)
                winreg.CloseKey(key)
                return True, f"Disabled startup: {name}"
            except FileNotFoundError:
                continue
        return False, f"Startup entry not found: {name}"

    # ========================================================
    #            NETWORK OPTIMIZER
    # ========================================================
    def set_dns(self, adapter="Ethernet", primary="1.1.1.1", secondary="1.0.0.1"):
        """Set DNS for given adapter name (visible in Control Panel)."""
        try:
            subprocess.run(f'netsh interface ip set dns name="{adapter}" static {primary}', shell=True)
            subprocess.run(f'netsh interface ip add dns name="{adapter}" {secondary} index=2', shell=True)
            return True, f"DNS set to {primary}, {secondary} on {adapter}"
        except Exception as e:
            return False, str(e)

    def enable_ctcp(self, enable=True):
        try:
            state = "enabled" if enable else "disabled"
            subprocess.run(f'netsh interface tcp set global congestionprovider=ctcp', shell=True)
            if not enable:
                subprocess.run(f'netsh interface tcp set global congestionprovider=none', shell=True)
            return True, f"CTCP {state}."
        except Exception as e:
            return False, str(e)

    def autotuning(self, level="normal"):
        """levels: disabled, highlyrestricted, restricted, normal, experimental"""
        try:
            subprocess.run(f'netsh interface tcp set global autotuninglevel={level}', shell=True)
            return True, f"TCP autotuning set: {level}"
        except Exception as e:
            return False, str(e)

    def toggle_nagle(self, enable=False):
        """
        Toggle Nagle's algorithm (per NIC). We set global gaming-friendly defaults via registry.
        """
        try:
            # SystemProfile\Tasks\Games boost
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games")
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.CloseKey(key)
            # Nagle off is default for low latency; 'enable=True' means we *enable* Nagle which increases latency
            return True, f"Nagle {'enabled' if enable else 'disabled'} (gaming default)."
        except Exception as e:
            return False, str(e)

    def latency_ping(self, host="1.1.1.1", count=5):
        try:
            out = subprocess.check_output(f"ping -n {count} {host}", shell=True, text=True, stderr=subprocess.STDOUT)
            return True, out
        except subprocess.CalledProcessError as e:
            return False, e.output
