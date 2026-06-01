#!/usr/bin/env bash
# Build a SELF-CONTAINED "Skicom.app" — a double-clickable macOS app that
# carries its own Python runtime and a copy of the app code INSIDE the bundle.
# It never reaches into ~/Desktop, so macOS TCC (which blocks an unsigned app
# from reading Desktop files) can't break the launcher.
#
#   ./mac/build_app.sh                 # builds ~/Desktop/Skicom.app
#   ./mac/build_app.sh /path/Foo.app   # builds at a custom location
#
# Re-run any time; it rebuilds the bundle from scratch (idempotent).
# No PyInstaller / py2app — just a venv inside the bundle.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
APP="${1:-$HOME/Desktop/Skicom.app}"
PNG="$HERE/skicom_icon.png"

# ── Icon ────────────────────────────────────────────────────────────────────
# Pick a Python to draw the icon (prefer the project venv).
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo "→ Drawing icon…"
"$PY" "$HERE/make_icon.py" "$PNG" >/dev/null || {
  echo "  (Pillow not available — install with: $PY -m pip install Pillow)"; }

echo "→ Building .icns…"
WORK="$(mktemp -d)"
SET="$WORK/Skicom.iconset"
mkdir -p "$SET"
if [ -f "$PNG" ]; then
  sips -z 16 16     "$PNG" --out "$SET/icon_16x16.png"      >/dev/null
  sips -z 32 32     "$PNG" --out "$SET/icon_16x16@2x.png"   >/dev/null
  sips -z 32 32     "$PNG" --out "$SET/icon_32x32.png"      >/dev/null
  sips -z 64 64     "$PNG" --out "$SET/icon_32x32@2x.png"   >/dev/null
  sips -z 128 128   "$PNG" --out "$SET/icon_128x128.png"    >/dev/null
  sips -z 256 256   "$PNG" --out "$SET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$PNG" --out "$SET/icon_256x256.png"    >/dev/null
  sips -z 512 512   "$PNG" --out "$SET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512   "$PNG" --out "$SET/icon_512x512.png"    >/dev/null
  cp "$PNG" "$SET/icon_512x512@2x.png"
  iconutil -c icns "$SET" -o "$WORK/AppIcon.icns"
fi

# ── Assemble bundle (fresh) ───────────────────────────────────────────────────
echo "→ Assembling bundle: $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
[ -f "$WORK/AppIcon.icns" ] && cp "$WORK/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Skicom</string>
  <key>CFBundleDisplayName</key><string>Skicom</string>
  <key>CFBundleIdentifier</key><string>com.skicom.launcher</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>Skicom</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>LSMinimumSystemVersion</key><string>10.13</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

# ── Self-contained app code ───────────────────────────────────────────────────
# Copy ONLY the runtime files into the bundle (no venv, .git, reports, docs,
# mac, tests, __pycache__). Bundling data/ and templates/ next to the code keeps
# the app's existing relative paths (data/resorts.json, templates/home.html)
# working from inside the bundle.
echo "→ Bundling app code (self-contained)…"
APPDIR="$APP/Contents/Resources/app"
mkdir -p "$APPDIR"
for f in skicom.py server.py app.py renderer.py weather.py accommodations.py resorts.py llm.py requirements.txt; do
  cp "$REPO/$f" "$APPDIR/$f"
done
cp -R "$REPO/data" "$APPDIR/data"
cp -R "$REPO/templates" "$APPDIR/templates"

# ── Bundled Python runtime (venv inside the bundle) ───────────────────────────
echo "→ Creating bundled Python runtime + installing dependencies…"
echo "  (This downloads and installs packages — give it about a minute.)"
python3 -m venv "$APPDIR/.venv"
"$APPDIR/.venv/bin/pip" install --quiet --upgrade pip
"$APPDIR/.venv/bin/pip" install --quiet -r "$APPDIR/requirements.txt"

# ── Launcher ──────────────────────────────────────────────────────────────────
# Resolves everything RELATIVE TO ITSELF (inside the bundle). It never touches
# ~/Desktop, so TCC can't block it. Logs go to ~/Library/Logs/Skicom.log.
cat > "$APP/Contents/MacOS/Skicom" <<'LAUNCH'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources/app" && pwd)"
LOG="$HOME/Library/Logs/Skicom.log"
exec "$DIR/.venv/bin/python" "$DIR/app.py" >>"$LOG" 2>&1
LAUNCH
chmod +x "$APP/Contents/MacOS/Skicom"

# Nudge Finder/LaunchServices to pick up the new icon.
touch "$APP"

# ── Terminal command ──────────────────────────────────────────────────────────
# Also install a `skicom` command on PATH for terminal use. This points at the
# repo copy — fine for the terminal, which has Desktop access.
chmod +x "$HERE/skicom"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"
ln -sf "$HERE/skicom" "$BIN/skicom"

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "✓ Built $APP"
echo "  This bundle is SELF-CONTAINED: it carries its own Python runtime and a"
echo "  copy of the app code inside Contents/Resources/app. It never reads from"
echo "  your ~/Desktop, so macOS TCC won't break it."
echo "  Double-click Skicom.app to open Skicom in a native desktop window."
echo "  First launch: macOS Gatekeeper may block it (unsigned) — if so,"
echo "  right-click the app → Open, then confirm."
echo
echo "✓ Installed 'skicom' → $BIN/skicom"
case ":$PATH:" in
  *":$BIN:"*) echo "  Try:  skicom --serve" ;;
  *) echo "  Note: $BIN is not on your PATH. Add it, or run: '$HERE/skicom' --serve" ;;
esac
