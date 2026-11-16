# PyInstaller recipe for the downloadable Foreign Language News Reader app.
#
#   pyinstaller packaging/foreign-language-news-reader.spec --noconfirm
#
# Run from the repository root, after downloading the voice into voices/:
#   python -m piper.download_voices --data-dir voices fr_FR-siwis-medium
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent
VOICE = "fr_FR-siwis-medium"

datas = [
    (str(ROOT / "voices" / f"{VOICE}.onnx"), "voices"),
    (str(ROOT / "voices" / f"{VOICE}.onnx.json"), "voices"),
    (str(ROOT / "packaging" / "icon.png"), "."),
    (str(ROOT / "LICENSE"), "."),
]
binaries, hiddenimports = [], []
# Packages with data files or compiled parts PyInstaller cannot see by itself.
for package in ("piper", "onnxruntime", "anthropic", "certifi"):
    found = collect_all(package)
    datas += found[0]
    binaries += found[1]
    hiddenimports += found[2]

icon = {"win32": "icon.ico", "darwin": "icon.icns"}.get(sys.platform, "icon.png")

a = Analysis(
    [str(ROOT / "news_reader.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "IPython", "matplotlib", "PIL"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="foreign-language-news-reader",
    console=False,  # a window app: no terminal appears on Windows or macOS
    icon=str(ROOT / "packaging" / icon),
)
coll = COLLECT(exe, a.binaries, a.datas, name="foreign-language-news-reader")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Foreign Language News Reader.app",
        icon=str(ROOT / "packaging" / "icon.icns"),
        bundle_identifier="io.github.foreign-language-news-reader",
        info_plist={"CFBundleShortVersionString": "1.1.2",
                    "NSHighResolutionCapable": True},
    )
