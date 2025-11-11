# Windows acrylic/blur using SetWindowCompositionAttribute via ctypes.
import ctypes, sys
from ctypes import wintypes

if sys.platform.startswith("win"):
    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [("AccentState", ctypes.c_int),
                    ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_int),
                    ("AnimationId", ctypes.c_int)]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        _fields_ = [("Attribute", ctypes.c_int),
                    ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t)]

    SetWindowCompositionAttribute = ctypes.windll.user32.SetWindowCompositionAttribute
    SetWindowCompositionAttribute.restype = wintypes.BOOL

    WCA_ACCENT_POLICY = 19
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4  # Win10 1803+

def enable_acrylic(hwnd: int, hex_color: int = 0xCC10131A, acrylic: bool = True):
    """hex_color is ABGR. 0xCC10131A ~= 80% alpha over dark blue-gray."""
    if not sys.platform.startswith("win"): return
    accent = ACCENTPOLICY()
    accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND if acrylic else ACCENT_ENABLE_BLURBEHIND
    accent.GradientColor = hex_color
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WCA_ACCENT_POLICY
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.addressof(accent)
    SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
