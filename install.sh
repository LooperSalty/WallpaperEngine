#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "Installing WallpaperEngine..."

# Check dependencies
for dep in python3 gtk4-layer-shell; do
    if ! python3 -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw" 2>/dev/null; then
        echo "Missing dependency: PyGObject with GTK 4 and libadwaita"
        echo "Install with: sudo pacman -S python-gobject gtk4 libadwaita"
        exit 1
    fi
    break
done

# Install scripts
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/wallpaper-selector.py" "$INSTALL_DIR/wallpaper-selector.py"
chmod +x "$INSTALL_DIR/wallpaper-selector.py"
cp "$SCRIPT_DIR/wallpaper-restore.sh" "$INSTALL_DIR/wallpaper-restore.sh"
chmod +x "$INSTALL_DIR/wallpaper-restore.sh"

# Install desktop entry
mkdir -p "$APP_DIR"
sed "s|Exec=.*|Exec=python3 $INSTALL_DIR/wallpaper-selector.py|" \
    "$SCRIPT_DIR/wallpaperengine.desktop" > "$APP_DIR/wallpaperengine.desktop"

# Update desktop database
update-desktop-database "$APP_DIR" 2>/dev/null || true

# Install systemd service for wallpaper restore on login
mkdir -p "$SYSTEMD_DIR"
cp "$SCRIPT_DIR/wallpaper-engine-restore.service" "$SYSTEMD_DIR/"
systemctl --user daemon-reload
systemctl --user enable wallpaper-engine-restore.service

echo "Installed to $INSTALL_DIR/"
echo "Desktop entry added — WallpaperEngine should appear in your app launcher."
echo "Systemd service enabled — wallpaper will be restored on login."
