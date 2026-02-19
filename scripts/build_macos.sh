#!/usr/bin/env bash
# Build macOS .app bundle and .dmg installer
# Run from the project root: ./scripts/build_macos.sh
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script must be run on macOS."
    echo "PyInstaller cannot cross-compile — build on the target platform."
    exit 1
fi

APP_NAME="Patreon Credits Generator"
DMG_NAME="PatreonCredits"
VERSION="1.1.0"

echo "=== Building macOS app ==="
python -m PyInstaller patreon_credits.spec --noconfirm

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: $APP_PATH not found. PyInstaller build failed."
    exit 1
fi

echo "=== Creating DMG ==="
DMG_DIR="dist/dmg"
DMG_OUTPUT="dist/${DMG_NAME}_${VERSION}.dmg"

# Clean previous
rm -rf "$DMG_DIR" "$DMG_OUTPUT"
mkdir -p "$DMG_DIR"

# Copy .app into staging dir
cp -R "$APP_PATH" "$DMG_DIR/"

# Add Applications symlink for drag-and-drop install
ln -s /Applications "$DMG_DIR/Applications"

# Copy .env.example alongside the app
cp .env.example "$DMG_DIR/"

# Create the DMG
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "$DMG_OUTPUT"

# Clean staging
rm -rf "$DMG_DIR"

echo ""
echo "=== Done ==="
echo "DMG: $DMG_OUTPUT"
echo "Size: $(du -h "$DMG_OUTPUT" | cut -f1)"
