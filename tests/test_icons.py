"""Ensure Windows can select native frames for common taskbar DPI scales."""

from pathlib import Path
import hashlib

from PIL import Image


def test_ico_covers_taskbar_and_titlebar_dpi_sizes():
    path = Path(__file__).resolve().parents[1] / "assets" / "logo.ico"
    with Image.open(path) as icon:
        sizes = {16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 96, 128, 256}
        assert icon.ico.sizes() == {(size, size) for size in sizes}
        for size in sizes:
            frame = icon.ico.getimage((size, size))
            assert frame.size == (size, size)


def test_ico_preserves_original_artwork():
    assets = Path(__file__).resolve().parents[1] / "assets"
    # The original artwork shipped in v1.0.0 must remain byte-for-byte unchanged.
    assert hashlib.sha256((assets / "logo.png").read_bytes()).hexdigest() == (
        "e54cba3cfd58e69e323f3ce2dccc46338969157171026c5a57f237b244c6022c"
    )
    with Image.open(assets / "logo.png") as original, Image.open(assets / "logo.ico") as icon:
        expected = original.resize((256, 256), Image.Resampling.LANCZOS).convert("RGBA")
        assert icon.ico.getimage((256, 256)).convert("RGBA").tobytes() == expected.tobytes()
    with Image.open(assets / "logo-window.png") as window_icon:
        assert window_icon.convert("RGBA").tobytes() == expected.tobytes()
