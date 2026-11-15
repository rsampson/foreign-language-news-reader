#!/bin/sh
# Installs French News Reader for the current user. No administrator
# password is needed and nothing outside your home folder is touched.
#
#   ./install.sh              install (or update)
#   ./install.sh --uninstall  remove the app; your settings are kept
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
APP_DIR=$DATA/french-news-reader/app
BIN=$HOME/.local/bin
LAUNCHER=$DATA/applications/french-news-reader.desktop
ICON=$DATA/icons/hicolor/512x512/apps/french-news-reader.png

if [ "${1:-}" = "--uninstall" ]; then
    rm -rf "$APP_DIR"
    rm -f "$BIN/french-news-reader" "$LAUNCHER" "$ICON"
    echo "French News Reader was removed."
    echo "Your settings and saved stories remain in $DATA/french-news-reader"
    exit 0
fi

if [ ! -x "$HERE/french-news-reader/french-news-reader" ]; then
    echo "Run this script from the folder you unpacked the download into." >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN" "$(dirname "$LAUNCHER")" "$(dirname "$ICON")"
rm -rf "$APP_DIR"
cp -R "$HERE/french-news-reader" "$APP_DIR"
ln -sf "$APP_DIR/french-news-reader" "$BIN/french-news-reader"
cp "$HERE/icon.png" "$ICON"

cat > "$LAUNCHER" <<LAUNCHER_END
[Desktop Entry]
Type=Application
Name=French News Reader
Comment=Learn French by reading the news side by side in French and English
Exec="$APP_DIR/french-news-reader"
Icon=french-news-reader
Terminal=false
Categories=Education;Languages;
StartupWMClass=french-news-reader
LAUNCHER_END

command -v update-desktop-database >/dev/null 2>&1 \
    && update-desktop-database "$(dirname "$LAUNCHER")" >/dev/null 2>&1 || true

echo "French News Reader is installed."
echo "Find it in your applications menu, or type: french-news-reader"
case ":$PATH:" in
    *":$BIN:"*) ;;
    *) echo "Note: $BIN is not on your PATH, so the typed command will work"
       echo "only after you log out and back in (or add it to your PATH)." ;;
esac
