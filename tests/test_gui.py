"""Layout regressions; require a desktop display (skip on headless systems)."""

import tkinter as tk
import sys
from types import SimpleNamespace

import pytest

from jv_analyzer.gui import App


@pytest.fixture(scope="module")
def app():
    try:
        window = App()
    except tk.TclError as error:
        if "display" in str(error).lower():
            pytest.skip(f"No desktop display: {error}")
        raise
    yield window
    window.destroy()


def resize(app, width, height):
    app.notebook.select(app.plot_panel)
    app.geometry(f"{width}x{height}+0+0")
    app.update()
    app._apply_layout()
    app.update()


def assert_visible_inside(widget, parent):
    assert widget.winfo_ismapped()
    x = widget.winfo_rootx() - parent.winfo_rootx()
    y = widget.winfo_rooty() - parent.winfo_rooty()
    assert x >= 0 and y >= 0
    assert x + widget.winfo_width() <= parent.winfo_width()
    assert y + widget.winfo_height() <= parent.winfo_height()


@pytest.mark.parametrize("width,height", [(1024, 600), (800, 600), (640, 480), (560, 360)])
def test_small_windows_keep_plot_toolbar_results_and_status_accessible(app, width, height):
    resize(app, width, height)
    siblings = app.workspace.winfo_children()
    assert siblings.index(app.plot_panel) > siblings.index(app.notebook)
    assert_visible_inside(app.plot_panel, app)
    assert_visible_inside(app.toolbar, app)
    for button in app.toolbar._buttons.values():
        assert_visible_inside(button, app.toolbar)
    status_label = next(widget for widget in app.winfo_children() if widget is not app.workspace)
    assert_visible_inside(status_label, app)
    if str(app.results_panel) in app.notebook.tabs():
        app.notebook.select(app.results_panel)
        app.update()
    assert_visible_inside(app.results_panel, app)
    assert_visible_inside(app.text, app.results_panel)


def test_layout_changes_preserve_inputs_plot_and_results(app):
    app.vars["area_cm2"].set("0.25")
    app.text.insert("end", "Voc: 1.1 V\n" * 60)
    line, = app.ax.plot([0, 1], [20, 0])
    sidebar = app._settings_width + app._plot_width + 40
    for width, expected in [(sidebar + app._results_width + 20, "wide"),
                            (sidebar + 10, "compact"), (560, "tabs"),
                            (sidebar + app._results_width + 20, "wide")]:
        resize(app, width, 480)
        assert app._layout_mode == expected
        assert app.vars["area_cm2"].get() == "0.25"
        assert "Voc: 1.1 V" in app.text.get("1.0", "end")
        assert line in app.ax.lines
    app.text.yview_moveto(1)
    app.update()
    assert app.text.yview()[0] > 0


def test_short_window_can_scroll_to_last_settings_action(app):
    resize(app, 560, 360)
    app.notebook.select(app.settings_panel)
    app.update()
    canvas = app.settings_canvas
    assert app.settings_content.winfo_height() > canvas.winfo_height()
    event = SimpleNamespace(widget=canvas, delta=-120, num="??")
    assert app._scroll_settings(event) == "break"
    assert canvas.yview()[0] > 0
    canvas.yview_moveto(1)
    app.update()
    save_button = next(widget for widget in app.settings_content.winfo_children()
                       if widget.cget("text") == "Save plot")
    assert_visible_inside(save_button, canvas)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows taskbar icons")
def test_native_window_has_small_and_taskbar_icons(app):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32")
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    hwnd = user32.GetAncestor(app.winfo_id(), 2)
    small = user32.SendMessageW(hwnd, 0x7F, 0, 0)  # WM_GETICON
    large = user32.SendMessageW(hwnd, 0x7F, 1, 0)
    assert small and large and small != large
