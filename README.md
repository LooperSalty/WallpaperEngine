# WallpaperEngine

GTK4/libadwaita GUI to browse, preview and apply [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/) wallpapers on Linux using [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine).

![GTK4](https://img.shields.io/badge/GTK4-libadwaita-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Browse all installed Workshop wallpapers with thumbnail previews
- Scene/Video type badge on each wallpaper
- Per-monitor wallpaper selection (apply different wallpapers to different screens)
- FPS control and silent mode
- Manages `linux-wallpaperengine` processes automatically

## Dependencies

- Python 3
- PyGObject (`python-gobject`)
- GTK 4 (`gtk4`)
- libadwaita (`libadwaita`)
- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine)
- Wallpaper Engine (Steam, with Workshop wallpapers subscribed)

### Arch Linux

```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

## Install

```bash
git clone https://github.com/LooperSalty/WallpaperEngine.git
cd WallpaperEngine
./install.sh
```

This installs the script to `~/.local/bin/` and adds a desktop entry so WallpaperEngine appears in your app launcher.

## Usage

Launch from your app launcher or run directly:

```bash
python3 ~/.local/bin/wallpaper-selector.py
```

1. Select a wallpaper from the grid
2. Check which monitor(s) to apply it to (DP-1, HDMI-A-1, or both)
3. Adjust FPS if needed
4. Click **Apply**

To set different wallpapers per monitor, check only one monitor at a time and apply separately.

## Configuration

Wallpapers are read from the default Steam Workshop directory:

```
~/.local/share/Steam/steamapps/workshop/content/431960/
```
