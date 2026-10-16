# Build from any working directory; include icons and the Tk plotting backend.
from pathlib import Path

root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "assets"), "assets")],
    hiddenimports=["openpyxl", "matplotlib.backends.backend_svg"],
    hooksconfig={"matplotlib": {"backends": ["TkAgg"]}},
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="JV_Analyzer",
    console=False,
    debug=False,
    strip=False,
    upx=False,
    icon=str(root / "assets" / "logo.ico"),
    version=str(root / "packaging" / "version_info.txt"),
)
