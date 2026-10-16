"""Ensure Windows can select native frames for common taskbar DPI scales."""

from pathlib import Path

from PIL import Image


def test_ico_covers_taskbar_and_titlebar_dpi_sizes():
    path = Path(__file__).resolve().parents[1] / "assets" / "logo.ico"
    with Image.open(path) as icon:
        sizes = {16, 20, 24, 28, 32, 40, 48, 56, 64, 96, 128, 256}
        assert icon.ico.sizes() == {(size, size) for size in sizes}
        for size in sizes:
            frame = icon.ico.getimage((size, size))
            assert frame.size == (size, size)
            # Artwork occupies nearly the whole frame, with transparent corners.
            x0, y0, x1, y1 = frame.getbbox()
            assert x1 - x0 >= size * 0.85
            assert y1 - y0 >= size * 0.85
            assert frame.getpixel((0, 0))[3] == 0
