"""Preserve the original artwork and give Windows a full-resolution icon."""

import ctypes
from ctypes import wintypes
import sys


def configure_process():
    if sys.platform != "win32":
        return
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
    shell32.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.c_long
    shell32.SetCurrentProcessExplicitAppUserModelID("CPVT.JVAnalyzer.Desktop")


def set_window_icons(window, path):
    """Load ICON_BIG at 256 px after Tk has mapped its native wrapper."""
    if sys.platform != "win32":
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR,
                                wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    user32.DestroyIcon.argtypes = [wintypes.HANDLE]
    user32.DestroyIcon.restype = wintypes.BOOL

    handles = []

    def apply(event=None):
        if (event is not None and event.widget is not window) or handles:
            return
        hwnd = user32.GetParent(window.winfo_id())
        if not hwnd:
            return
        small_size = user32.GetSystemMetrics(49)  # SM_CXSMICON
        loaded = []
        for kind, size in ((0, small_size), (1, 256)):
            icon = user32.LoadImageW(None, str(path), 1, size, size, 0x10)
            if not icon:
                error = ctypes.get_last_error()
                for _, handle in loaded:
                    user32.DestroyIcon(handle)
                raise ctypes.WinError(error)
            loaded.append((kind, icon))
        for kind, icon in loaded:
            user32.SendMessageW(hwnd, 0x80, kind, icon)  # WM_SETICON
            handles.append(icon)

    def cleanup(event):
        if event.widget is window:
            for handle in handles:
                user32.DestroyIcon(handle)
            handles.clear()

    window.bind("<Map>", apply, add="+")
    window.bind("<Destroy>", cleanup, add="+")
    if window.winfo_ismapped():
        apply()


def taskbar_icon_size(window):
    """Read the actual ICON_BIG bitmap size for diagnostics, including frozen builds."""
    if sys.platform != "win32":
        return None

    class IconInfo(ctypes.Structure):
        _fields_ = [("is_icon", wintypes.BOOL), ("x", wintypes.DWORD),
                    ("y", wintypes.DWORD), ("mask", wintypes.HBITMAP),
                    ("color", wintypes.HBITMAP)]

    class Bitmap(ctypes.Structure):
        _fields_ = [("type", wintypes.LONG), ("width", wintypes.LONG),
                    ("height", wintypes.LONG), ("width_bytes", wintypes.LONG),
                    ("planes", wintypes.WORD), ("bits_pixel", wintypes.WORD),
                    ("bits", ctypes.c_void_p)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(IconInfo)]
    user32.GetIconInfo.restype = wintypes.BOOL
    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p]
    gdi32.GetObjectW.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
    gdi32.DeleteObject.restype = wintypes.BOOL

    hwnd = user32.GetParent(window.winfo_id())
    icon = user32.SendMessageW(hwnd, 0x7F, 1, 0)  # WM_GETICON / ICON_BIG
    info = IconInfo()
    if not user32.GetIconInfo(icon, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        bitmap = Bitmap()
        if not gdi32.GetObjectW(info.color, ctypes.sizeof(bitmap), ctypes.byref(bitmap)):
            raise ctypes.WinError(ctypes.get_last_error())
        return bitmap.width, bitmap.height
    finally:
        for handle in (info.color, info.mask):
            if handle:
                gdi32.DeleteObject(handle)
