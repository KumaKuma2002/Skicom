#!/usr/bin/env bash
#
# sign_local.sh — Reduce macOS Gatekeeper friction for a locally-built,
# UNSIGNED Skicom.app.
#
# This does NOT make the app distributable. It only ad-hoc signs the app and
# strips quarantine so YOU can run your own local build without nag screens.
#
set -euo pipefail

# 1) Resolve the app path (arg 1, default to ~/Desktop/Skicom.app).
APP="${1:-$HOME/Desktop/Skicom.app}"

if [[ ! -e "$APP" ]]; then
  echo "Error: app not found at: $APP" >&2
  echo "Usage: $0 [/path/to/Skicom.app]" >&2
  exit 1
fi

echo "==> Target app: $APP"

# 2) Remove the quarantine attribute recursively (ignore if it's not set).
echo "==> Removing quarantine attribute (if present)..."
xattr -dr com.apple.quarantine "$APP" || true

# 3) Apply an ad-hoc code signature ("-" is the ad-hoc identity).
#    --force overwrites any existing sig, --deep covers nested code.
if command -v codesign >/dev/null 2>&1; then
  echo "==> Applying ad-hoc code signature..."
  codesign --force --deep --sign - "$APP"

  # 4) Verify the signature (best-effort; don't abort on failure).
  echo "==> Verifying signature..."
  if codesign --verify --deep --strict "$APP" 2>&1; then
    echo "    Signature verified OK."
  else
    echo "    Warning: signature verification reported issues (continuing)."
  fi
else
  echo "Warning: 'codesign' not available — skipping ad-hoc signing." >&2
fi

# 5) Tell the user what just happened and how to bypass Gatekeeper if needed.
cat <<'EOF'

==> Done.

NOTE: This app is self-signed / ad-hoc for LOCAL use only. It is NOT
notarized or distributable — only the machine that built it should trust it.

If macOS still blocks the app on first launch, you can:
  - Right-click the app in Finder -> Open -> Open (confirm the dialog), or
  - Allow it under System Settings -> Privacy & Security (scroll down and
    click "Open Anyway").
EOF
