"""Windows taskbar identity and icons sized for the display DPI."""

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
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetProcessDpiAwarenessContext.argtypes = [wintypes.HANDLE]
    user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
    # System DPI awareness prevents Windows from stretching a low-resolution window.
    # A false return is normal when the host has already configured DPI awareness.
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-2))


def set_window_icons(window, path):
    if sys.platform != "win32":
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetDpiForWindow.argtypes = [wintypes.HWND]
    user32.GetDpiForWindow.restype = wintypes.UINT
    user32.GetSystemMetricsForDpi.argtypes = [ctypes.c_int, wintypes.UINT]
    user32.GetSystemMetricsForDpi.restype = ctypes.c_int
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR,
                                wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    user32.DestroyIcon.argtypes = [wintypes.HANDLE]
    user32.DestroyIcon.restype = wintypes.BOOL

    window.update_idletasks()
    hwnd = user32.GetAncestor(window.winfo_id(), 2)  # GA_ROOT: Tk's native top-level wrapper.
    dpi = user32.GetDpiForWindow(hwnd) or 96
    handles = []
    for kind, x_metric, y_metric in ((0, 49, 50), (1, 11, 12)):
        width = user32.GetSystemMetricsForDpi(x_metric, dpi)
        height = user32.GetSystemMetricsForDpi(y_metric, dpi)
        icon = user32.LoadImageW(None, str(path), 1, width, height, 0x10)
        if not icon:
            for handle in handles:
                user32.DestroyIcon(handle)
            raise ctypes.WinError(ctypes.get_last_error())
        user32.SendMessageW(hwnd, 0x80, kind, icon)  # WM_SETICON, small / taskbar.
        handles.append(icon)

    def cleanup(event):
        if event.widget is window:
            for handle in handles:
                user32.DestroyIcon(handle)

    window.bind("<Destroy>", cleanup, add="+")
