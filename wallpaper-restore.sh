#!/bin/bash
# Restore the last applied Wallpaper Engine wallpaper on login.

STATE_FILE="$HOME/.config/wallpaper-engine/state.json"
WORKSHOP_DIR="$HOME/.local/share/Steam/steamapps/workshop/content/431960"
WE_BIN="linux-wallpaperengine"

if [ ! -f "$STATE_FILE" ]; then
    echo "No saved wallpaper state, nothing to restore."
    exit 0
fi

if ! command -v "$WE_BIN" &>/dev/null; then
    echo "$WE_BIN not found."
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "jq not found."
    exit 1
fi

WORKSHOP_ID=$(jq -r '.workshop_id' "$STATE_FILE")
FPS=$(jq -r '.fps' "$STATE_FILE")
SILENT=$(jq -r '.silent' "$STATE_FILE")
readarray -t SCREENS < <(jq -r '.screens[]' "$STATE_FILE")

WP_DIR="$WORKSHOP_DIR/$WORKSHOP_ID"
if [ ! -d "$WP_DIR" ]; then
    echo "Wallpaper directory not found: $WP_DIR"
    exit 1
fi

# Kill any existing linux-wallpaperengine processes
pkill -x "$WE_BIN" 2>/dev/null
sleep 1

for SCREEN in "${SCREENS[@]}"; do
    CMD=("$WE_BIN" "--fps" "$FPS" "--no-fullscreen-pause")
    if [ "$SILENT" = "true" ]; then
        CMD+=("--silent")
    fi
    CMD+=("--screen-root" "$SCREEN" "$WP_DIR")

    echo "Restoring wallpaper on $SCREEN: $WORKSHOP_ID (${FPS}fps)"
    "${CMD[@]}" &>/dev/null &
done
