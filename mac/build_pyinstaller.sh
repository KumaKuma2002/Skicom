#!/usr/bin/env bash
# Build a FULLY-FROZEN, self-contained "Skicom.app" via PyInstaller — the
# "Plan B" alternative to ./mac/build_app.sh.
#
# Where build_app.sh ships a real venv inside the bundle, this freezes the
# whole app (Python interpreter + every dependency) into one self-contained
# Skicom.app. The target Mac needs NO Python installed.
#
#   ./mac/build_pyinstaller.sh
#
# The result lands at mac/dist/Skicom.app. This script does NOT touch your
# existing ~/Desktop/Skicom.app (that's Plan A's output) — drag the new app
# wherever you like. Re-run any time; it's idempotent (--clean rebuild).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../Skicom/mac
REPO="$(cd "$HERE/.." && pwd)"                          # repo root
PY="$REPO/.venv/bin/python"
PIP="$REPO/.venv/bin/pip"
PNG="$HERE/skicom_icon.png"
ICNS="$HERE/AppIcon.icns"

# ── Icon ──────────────────────────────────────────────────────────────────
# Draw the source PNG (best-effort — needs Pillow), then turn it into an
# .icns the spec will pick up. Guarded so a missing Pillow won't abort.
echo "→ Drawing icon…"
"$PY" "$HERE/make_icon.py" "$PNG" >/dev/null 2>&1 || \
  echo "  (Pillow not available — skipping icon art; app will use a default icon)"

if [ -f "$PNG" ]; then
  echo "→ Building .icns…"
  WORK="$(mktemp -d)"
  SET="$WORK/Skicom.iconset"
  mkdir -p "$SET"
  sips -z 16 16     "$PNG" --out "$SET/icon_16x16.png"      >/dev/null
  sips -z 32 32     "$PNG" --out "$SET/icon_16x16@2x.png"   >/dev/null
  sips -z 32 32     "$PNG" --out "$SET/icon_32x32.png"      >/dev/null
  sips -z 64 64     "$PNG" --out "$SET/icon_32x32@2x.png"   >/dev/null
  sips -z 128 128   "$PNG" --out "$SET/icon_128x128.png"    >/dev/null
  sips -z 256 256   "$PNG" --out "$SET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$PNG" --out "$SET/icon_256x256.png"    >/dev/null
  sips -z 512 512   "$PNG" --out "$SET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512   "$PNG" --out "$SET/icon_512x512.png"    >/dev/null
  sips -z 1024 1024 "$PNG" --out "$SET/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$SET" -o "$ICNS"
  rm -rf "$WORK"
  echo "  → $ICNS"
else
  echo "  (No $PNG — building without a custom icon)"
fi

# ── PyInstaller ─────────────────────────────────────────────────────────────
echo "→ Ensuring PyInstaller is available…"
"$PIP" install --quiet pyinstaller

echo "→ Freezing app with PyInstaller (this can take a minute)…"
"$PY" -m PyInstaller \
  --noconfirm --clean \
  "$HERE/Skicom.spec" \
  --distpath "$HERE/dist" \
  --workpath "$HERE/build"

APP="$HERE/dist/Skicom.app"

# ── Summary ───────────────────────────────────────────────────────────────
echo
if [ -d "$APP" ]; then
  echo "✓ Built (fully frozen) $APP"
  echo "  This bundle carries its own Python — the target Mac needs NO Python."
  echo "  Drag Skicom.app to /Applications or your Desktop to install it."
  echo "  First launch: macOS Gatekeeper may block it (unsigned) — if so,"
  echo "  right-click the app → Open, then confirm."
  echo
  echo "  Note: this is the FULLY-FROZEN alternative to ./mac/build_app.sh."
  echo "  It is left in mac/dist/ and does NOT overwrite ~/Desktop/Skicom.app."
else
  echo "✗ Build finished but $APP was not found — check the PyInstaller output above."
  exit 1
fi
