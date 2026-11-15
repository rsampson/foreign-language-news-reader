#!/bin/sh
# Installs Foreign Language News Reader for the current user. No administrator
# password is needed and nothing outside your home folder is touched.
#
#   ./install.sh              install (or update)
#   ./install.sh --uninstall  remove the app; your settings are kept
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
APP_DIR=$DATA/foreign-language-news-reader/app
BIN=$HOME/.local/bin
LAUNCHER=$DATA/applications/foreign-language-news-reader.desktop
ICON=$DATA/icons/hicolor/512x512/apps/foreign-language-news-reader.png

if [ "${1:-}" = "--uninstall" ]; then
    rm -rf "$APP_DIR"
    rm -f "$BIN/foreign-language-news-reader" "$LAUNCHER" "$ICON"
    echo "Foreign Language News Reader was removed."
    echo "Your settings and saved stories remain in $DATA/foreign-language-news-reader"
    exit 0
fi

if [ ! -x "$HERE/foreign-language-news-reader/foreign-language-news-reader" ]; then
    echo "Run this script from the folder you unpacked the download into." >&2
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN" "$(dirname "$LAUNCHER")" "$(dirname "$ICON")"
rm -rf "$APP_DIR"
cp -R "$HERE/foreign-language-news-reader" "$APP_DIR"
ln -sf "$APP_DIR/foreign-language-news-reader" "$BIN/foreign-language-news-reader"
cp "$HERE/icon.png" "$ICON"

cat > "$LAUNCHER" <<LAUNCHER_END
[Desktop Entry]
Type=Application
Name=Foreign Language News Reader
Comment=Learn French by reading the news side by side in French and English
Exec="$APP_DIR/foreign-language-news-reader"
Icon=foreign-language-news-reader
Terminal=false
Categories=Education;Languages;
StartupWMClass=foreign-language-news-reader
LAUNCHER_END

command -v update-desktop-database >/dev/null 2>&1 \
    && update-desktop-database "$(dirname "$LAUNCHER")" >/dev/null 2>&1 || true

echo "Foreign Language News Reader is installed."
echo "Find it in your applications menu, or type: foreign-language-news-reader"
case ":$PATH:" in
    *":$BIN:"*) ;;
    *) echo "Note: $BIN is not on your PATH, so the typed command will work"
       echo "only after you log out and back in (or add it to your PATH)." ;;
esac
