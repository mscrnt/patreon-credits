#!/usr/bin/env bash
# Build Linux AppImage
# Run from the project root: ./scripts/build_linux.sh
set -euo pipefail

if [[ "$(uname)" != "Linux" ]]; then
    echo "ERROR: This script must be run on Linux."
    echo "PyInstaller cannot cross-compile — build on the target platform."
    exit 1
fi

APP_NAME="PatreonCredits"
VERSION="1.1.0"
APPDIR="dist/${APP_NAME}.AppDir"

echo "=== Building Linux binary ==="
python -m PyInstaller patreon_credits.spec --noconfirm

BINARY="dist/${APP_NAME}"
if [ ! -f "$BINARY" ]; then
    echo "ERROR: $BINARY not found. PyInstaller build failed."
    exit 1
fi

echo "=== Creating AppDir ==="
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "$BINARY" "$APPDIR/usr/bin/${APP_NAME}"
chmod +x "$APPDIR/usr/bin/${APP_NAME}"

# Copy .env.example alongside
cp .env.example "$APPDIR/usr/bin/"

# Desktop entry
cat > "$APPDIR/${APP_NAME}.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=Patreon Credits Generator
Comment=Generate scrolling credits videos for Patreon supporters
Exec=PatreonCredits
Icon=PatreonCredits
Categories=AudioVideo;Video;
Terminal=false
DESKTOP

# AppRun launcher
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/usr/bin/env bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/PatreonCredits" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Generate a simple icon (solid red square with PC text) if no icon exists
if command -v python3 &>/dev/null; then
    python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (256, 256), (255, 66, 77, 255))
d = ImageDraw.Draw(img)
d.text((60, 90), 'PC', fill=(255, 255, 255))
img.save('$APPDIR/PatreonCredits.png')
img.save('$APPDIR/usr/share/icons/hicolor/256x256/apps/PatreonCredits.png')
" 2>/dev/null || {
        # Fallback: create a 1x1 placeholder
        printf '\x89PNG\r\n\x1a\n' > "$APPDIR/PatreonCredits.png"
        cp "$APPDIR/PatreonCredits.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/PatreonCredits.png"
    }
else
    printf '\x89PNG\r\n\x1a\n' > "$APPDIR/PatreonCredits.png"
    cp "$APPDIR/PatreonCredits.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/PatreonCredits.png"
fi

echo "=== Downloading appimagetool ==="
ARCH=$(uname -m)
TOOL="dist/appimagetool-${ARCH}.AppImage"
if [ ! -f "$TOOL" ]; then
    curl -fSL -o "$TOOL" \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x "$TOOL"
fi

echo "=== Building AppImage ==="
APPIMAGE="dist/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
ARCH="$ARCH" "$TOOL" "$APPDIR" "$APPIMAGE" --no-appstream 2>/dev/null || \
ARCH="$ARCH" "$TOOL" "$APPDIR" "$APPIMAGE"

# Clean up
rm -rf "$APPDIR"

echo ""
echo "=== Done ==="
echo "AppImage: $APPIMAGE"
echo "Size: $(du -h "$APPIMAGE" | cut -f1)"
echo ""
echo "Users run it with: chmod +x ${APP_NAME}-${VERSION}-${ARCH}.AppImage && ./${APP_NAME}-${VERSION}-${ARCH}.AppImage"
