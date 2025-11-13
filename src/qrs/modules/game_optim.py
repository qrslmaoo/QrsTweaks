"""
src/qrs/modules/game_optim.py

Backend logic for per-game optimization, starting with:
- Global "gaming" tweaks (Game Bar / DVR / FSO / low latency)
- GPU scheduling
- Basic Nvidia / AMD / Intel detection (via WMI / registry)
- Fortnite-specific cache cleanup (shader + logs)
- DirectX cache cleanup

All methods are defensive:
- They never raise exceptions to the caller.
- They return (ok: bool, message: str) for logging in the UI.

NO AI, NO monitoring, NO background services.
Everything is on-demand, one-shot tweaks.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _run_reg_add(
    key: str,
    name: str,
    data_type: str,
    value: str,
) -> Tuple[bool, str]:
    """
    Run a 'reg add' safely. Returns (ok, message).
    data_type e.g. REG_DWORD, REG_SZ.
    """
    try:
        cmd = [
            "reg",
            "add",
            key,
            "/v",
            name,
            "/t",
            data_type,
            "/d",
            str(value),
            "/f",
        ]
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,
        )
        if cp.returncode == 0:
            return True, f"Registry set: {key}\\{name} = {value} ({data_type})"
        return False, f"Failed to set registry {key}\\{name}: {cp.stderr.strip()}"
    except FileNotFoundError:
        return False, "reg.exe not found (non-Windows or restricted environment)."
    except Exception as e:
        return False, f"Registry operation error: {e}"


def _delete_dir_safe(path: Path) -> Tuple[bool, str]:
    """
    Delete a directory tree if it exists. Returns (ok, message).
    NEVER throws to caller.
    """
    try:
        if not path.exists():
            return True, f"{path} does not exist (nothing to delete)."
        shutil.rmtree(path, ignore_errors=True)
        return True, f"Deleted directory: {path}"
    except Exception as e:
        return False, f"Error deleting {path}: {e}"


def _is_windows() -> bool:
    return sys.platform.startswith("win32") or sys.platform.startswith("cygwin")


# ------------------------------------------------------------
# GPU detection (very lightweight)
# ------------------------------------------------------------

@dataclass
class GpuInfo:
    vendor: str  # "nvidia", "amd", "intel", "unknown"
    raw: str


def _detect_gpu_vendor() -> GpuInfo:
    """
    Very lightweight GPU vendor detection.
    - Uses 'wmic path win32_VideoController get Name' if available.
    - Never crashes; falls back to "unknown".
    """
    if not _is_windows():
        return GpuInfo(vendor="unknown", raw="non-windows")

    try:
        cp = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "Name"],
            capture_output=True,
            text=True,
            shell=False,
        )
        if cp.returncode != 0:
            return GpuInfo(vendor="unknown", raw=cp.stderr.strip() or cp.stdout.strip())
        text = (cp.stdout or "").lower()
        vendor = "unknown"
        if "nvidia" in text:
            vendor = "nvidia"
        elif "advanced micro devices" in text or "amd" in text or "radeon" in text:
            vendor = "amd"
        elif "intel" in text:
            vendor = "intel"
        return GpuInfo(vendor=vendor, raw=cp.stdout.strip())
    except Exception as e:
        return GpuInfo(vendor="unknown", raw=str(e))


# ------------------------------------------------------------
# Game Optimizer
# ------------------------------------------------------------

class GameOptimizer:
    """
    Core logic class for game-level optimizations.

    Constructor is intentionally minimal; profiles/logging/controllers
    are expected to be handled elsewhere.
    """

    def __init__(self):
        self.gpu_info: GpuInfo = _detect_gpu_vendor()

    # ============================================================
    #   GLOBAL GAMING TWEAKS (Game Bar / DVR / FSO / low latency)
    # ============================================================

    def disable_xbox_game_bar(self) -> Tuple[bool, str]:
        """
        Disable Xbox Game Bar overlay and capture.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak Game Bar."

        ok1, m1 = _run_reg_add(
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR",
            "AppCaptureEnabled",
            "REG_DWORD",
            "0",
        )
        ok2, m2 = _run_reg_add(
            r"HKCU\System\GameConfigStore",
            "GameDVR_Enabled",
            "REG_DWORD",
            "0",
        )

        ok = ok1 and ok2
        msg = "; ".join([m1, m2])
        return ok, f"[Game Bar] {msg}"

    def disable_game_dvr(self) -> Tuple[bool, str]:
        """
        Disable background Game DVR recording.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak Game DVR."

        ok1, m1 = _run_reg_add(
            r"HKCU\System\GameConfigStore",
            "GameDVR_DSEBehavior",
            "REG_DWORD",
            "2",
        )
        ok2, m2 = _run_reg_add(
            r"HKCU\System\GameConfigStore",
            "AllowGameDVR",
            "REG_DWORD",
            "0",
        )
        ok = ok1 and ok2
        msg = "; ".join([m1, m2])
        return ok, f"[Game DVR] {msg}"

    def disable_fullscreen_optimizations(self) -> Tuple[bool, str]:
        """
        Disable Fullscreen Optimizations globally.
        This reduces some input lag and odd frame pacing.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak FSO."

        ok, msg = _run_reg_add(
            r"HKCU\System\GameConfigStore",
            "GameDVR_FSEBehaviorMode",
            "REG_DWORD",
            "2",
        )
        return ok, f"[Fullscreen Optimizations] {msg}"

    def apply_low_latency_preset(self) -> Tuple[bool, str]:
        """
        Apply a low-latency preset:
        - Ensure DVR off
        - Ensure GameDVR not allowed
        - Sets FFXBuffering to 1 (low latency frame pacing)
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot apply latency preset."

        msgs = []
        ok_all = True

        # Reuse DVR disable function
        ok, msg = self.disable_game_dvr()
        msgs.append(msg)
        ok_all = ok_all and ok

        # FFXBuffering: 1 = low latency mode
        ok2, m2 = _run_reg_add(
            r"HKCU\System\GameConfigStore",
            "FFXBuffering",
            "REG_DWORD",
            "1",
        )
        ok_all = ok_all and ok2
        msgs.append(m2)

        return ok_all, "[Low Latency Preset] " + "; ".join(msgs)

    # ============================================================
    #   GPU SCHEDULING / PERFORMANCE
    # ============================================================

    def enable_gpu_scheduling(self) -> Tuple[bool, str]:
        """
        Enable Hardware-accelerated GPU scheduling:
        HwSchMode = 2 under GraphicsDrivers.
        """
        if not _is_windows():
            return False, "Not running on Windows; cannot tweak GPU scheduling."

        ok, msg = _run_reg_add(
            r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            "HwSchMode",
            "REG_DWORD",
            "2",
        )
        return ok, f"[GPU Scheduling] {msg}"

    def apply_nvidia_max_performance_hint(self) -> Tuple[bool, str]:
        """
        Very light Nvidia hint: this does NOT use NVAPI and does NOT
        attempt to modify driver profiles directly.

        Instead, it writes a safe REG value that some Nvidia builds
        respect as a default power policy hint. If GPU is not Nvidia,
        this becomes a no-op message.
        """
        if self.gpu_info.vendor != "nvidia":
            return True, "[Nvidia] GPU is not Nvidia; nothing to apply."

        if not _is_windows():
            return False, "Not running on Windows; cannot tweak Nvidia hints."

        # Some Nvidia drivers read this as a global perf hint
        key = r"HKLM\SYSTEM\CurrentControlSet\Services\nvlddmkm\Global"
        ok, msg = _run_reg_add(
            key,
            "PerfLevelSrc",
            "REG_DWORD",
            "3322",  # common 'prefer max performance' hint
        )
        return ok, f"[Nvidia Max Performance] {msg}"

    # ============================================================
    #   FORTNITE-SPECIFIC CLEANUPS
    # ============================================================

    def _local_appdata(self) -> Optional[Path]:
        lad = os.getenv("LOCALAPPDATA")
        return Path(lad) if lad else None

    def fortnite_paths(self) -> dict:
        """
        Returns key paths used for Fortnite cleanup.
        """
        lad = self._local_appdata()
        if not lad:
            return {}

        base = lad / "FortniteGame" / "Saved"
        return {
            "shader_cache": base / "ShaderCache",
            "logs": base / "Logs",
            "crashes": base / "Crashes",
            "config_backup": base / "Config_Backup_QrsTweaks",
        }

    def clean_fortnite_shader_cache(self) -> Tuple[bool, str]:
        """
        Delete Fortnite shader cache directory.
        """
        paths = self.fortnite_paths()
        if not paths:
            return False, "LOCALAPPDATA not found; cannot locate Fortnite shader cache."

        ok, msg = _delete_dir_safe(paths["shader_cache"])
        return ok, f"[Fortnite Shader Cache] {msg}"

    def clean_fortnite_logs_and_crashes(self) -> Tuple[bool, str]:
        """
        Delete Fortnite logs and crash dumps.
        """
        paths = self.fortnite_paths()
        if not paths:
            return False, "LOCALAPPDATA not found; cannot locate Fortnite logs."

        msgs = []
        ok_all = True

        for key in ("logs", "crashes"):
            ok, msg = _delete_dir_safe(paths[key])
            ok_all = ok_all and ok
            msgs.append(msg)

        return ok_all, "[Fortnite Logs/Crashes] " + "; ".join(msgs)

    # ============================================================
    #   DIRECTX / GLOBAL SHADER CACHES
    # ============================================================

    def clean_directx_cache(self) -> Tuple[bool, str]:
        """
        Clean DirectX cache under LOCALAPPDATA\\D3DSCache and other safe dirs.
        """
        lad = self._local_appdata()
        if not lad:
            return False, "LOCALAPPDATA not found; cannot clean DirectX cache."

        dx_cache = lad / "D3DSCache"
        ok, msg = _delete_dir_safe(dx_cache)
        return ok, f"[DirectX Cache] {msg}"

    # ============================================================
    #   HIGH-LEVEL PACKS
    # ============================================================

    def apply_fortnite_optimization_pack(self) -> Tuple[bool, str]:
        """
        High-level pack called from the UI:
        - Disable Game Bar
        - Disable DVR
        - Disable FSO
        - Apply low latency preset
        - Enable GPU scheduling
        - (If Nvidia) apply perf hint
        - Clean Fortnite shader cache
        - Clean Fortnite logs/crashes
        - Clean DirectX cache
        """
        if not _is_windows():
            return False, "Not running on Windows; Fortnite pack only supports Windows."

        results = []

        # Game Bar, DVR, FSO, latency
        for func in (
            self.disable_xbox_game_bar,
            self.disable_game_dvr,
            self.disable_fullscreen_optimizations,
            self.apply_low_latency_preset,
        ):
            ok, msg = func()
            results.append(msg)

        # GPU scheduling + Nvidia perf
        ok_gpu, msg_gpu = self.enable_gpu_scheduling()
        results.append(msg_gpu)

        ok_nv, msg_nv = self.apply_nvidia_max_performance_hint()
        results.append(msg_nv)

        # Fortnite cache cleanups
        ok_sh, msg_sh = self.clean_fortnite_shader_cache()
        results.append(msg_sh)

        ok_logs, msg_logs = self.clean_fortnite_logs_and_crashes()
        results.append(msg_logs)

        # DirectX cache
        ok_dx, msg_dx = self.clean_directx_cache()
        results.append(msg_dx)

        ok_all = all([
            ok_gpu,
            ok_nv,
            ok_sh,
            ok_logs,
            ok_dx,
        ])

        return ok_all, "\n".join(results)
