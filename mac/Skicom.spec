# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Skicom — the "Plan B" fully-frozen macOS build.
#
# This is an ALTERNATIVE to mac/build_app.sh. Where build_app.sh bundles a
# real venv inside the .app, this spec freezes the entire app (including the
# Python interpreter and every dependency) into a single self-contained
# Skicom.app via PyInstaller — so the target Mac needs NO Python installed.
#
# How data/templates resolution works under the freeze:
#   The app resolves its data and templates via each module's own __file__ dir:
#     - resorts.py:  os.path.join(os.path.dirname(__file__), "data", "resorts.json")
#     - server.py:   os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "home.html")
#   Under PyInstaller, a bundled module's __file__ dir is sys._MEIPASS (the
#   unpacked bundle root). The `datas` below place data/resorts.json and
#   templates/home.html at exactly that root (in 'data' and 'templates'), so
#   the app's existing relative paths keep working unchanged.
#   Reports are already written to a temp dir by server.py (tempfile.gettempdir()),
#   so there's no writable-cwd requirement for a read-only frozen bundle.

import os

# PyInstaller defines SPECPATH as the directory containing this spec file.
HERE = os.path.abspath(SPECPATH)            # .../Skicom/mac
REPO = os.path.abspath(os.path.join(HERE, os.pardir))  # repo root (parent of mac/)

ICON = os.path.join(HERE, "AppIcon.icns")
icon_path = ICON if os.path.exists(ICON) else None

block_cipher = None


a = Analysis(
    [os.path.join(REPO, "app.py")],
    pathex=[REPO],
    binaries=[],
    datas=[
        (os.path.join(REPO, "data", "resorts.json"), "data"),
        (os.path.join(REPO, "templates", "home.html"), "templates"),
    ],
    hiddenimports=[
        # pywebview's macOS backend is the Cocoa platform, driven by pyobjc.
        "webview",
        "webview.platforms.cocoa",
        "objc",
        "Foundation",
        "WebKit",
        "AppKit",
        # App dependencies that may be imported dynamically / via C extensions.
        "thefuzz",
        "Levenshtein",
        "jinja2",
        "yaml",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Skicom",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed (GUI) app — no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Skicom",
)

app = BUNDLE(
    coll,
    name="Skicom.app",
    icon=icon_path,
    bundle_identifier="com.skicom.app",
    info_plist={
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13",
        "CFBundleName": "Skicom",
        "CFBundleDisplayName": "Skicom",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1.0",
    },
)
