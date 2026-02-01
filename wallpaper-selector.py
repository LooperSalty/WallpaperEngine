#!/usr/bin/env python3
"""Wallpaper Engine Selector – GTK 4 / libadwaita GUI."""

import json
import os
import signal
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango

WORKSHOP_DIR = Path.home() / ".local/share/Steam/steamapps/workshop/content/431960"
WE_BIN = "linux-wallpaperengine"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
class WallpaperInfo:
    __slots__ = ("workshop_id", "title", "wp_type", "preview_path")

    def __init__(self, workshop_id: str, title: str, wp_type: str, preview_path: str):
        self.workshop_id = workshop_id
        self.title = title
        self.wp_type = wp_type
        self.preview_path = preview_path

    @staticmethod
    def from_directory(path: Path):
        project_file = path / "project.json"
        if not project_file.exists():
            return None
        try:
            with open(project_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        title = data.get("title", path.name)
        wp_type = data.get("type", "unknown").capitalize()
        preview = data.get("preview", "preview.jpg")
        preview_path = str(path / preview)
        return WallpaperInfo(path.name, title, wp_type, preview_path)


def discover_wallpapers() -> list[WallpaperInfo]:
    if not WORKSHOP_DIR.is_dir():
        return []
    results = []
    for entry in sorted(WORKSHOP_DIR.iterdir()):
        if entry.is_dir():
            info = WallpaperInfo.from_directory(entry)
            if info:
                results.append(info)
    return results


# ---------------------------------------------------------------------------
# Thumbnail card
# ---------------------------------------------------------------------------
class WallpaperCard(Gtk.Box):
    def __init__(self, info: WallpaperInfo):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.info = info

        # Overlay for badge
        overlay = Gtk.Overlay()
        overlay.set_size_request(320, 180)

        self.picture = Gtk.Picture()
        self.picture.set_size_request(320, 180)
        self.picture.set_content_fit(Gtk.ContentFit.COVER)
        overlay.set_child(self.picture)

        # Badge
        badge = Gtk.Label(label=info.wp_type)
        badge.add_css_class("badge")
        badge.set_halign(Gtk.Align.END)
        badge.set_valign(Gtk.Align.START)
        badge.set_margin_top(6)
        badge.set_margin_end(6)
        overlay.add_overlay(badge)

        self.append(overlay)

        # Title
        label = Gtk.Label(label=info.title)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(30)
        label.set_tooltip_text(info.title)
        self.append(label)

    def load_thumbnail(self):
        if os.path.isfile(self.info.preview_path):
            try:
                texture = Gdk.Texture.new_from_filename(self.info.preview_path)
                self.picture.set_paintable(texture)
            except GLib.Error:
                pass


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class WallpaperSelectorWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="WallpaperEngine")
        self.set_default_size(1100, 750)

        # One process per monitor
        self._processes: dict[str, subprocess.Popen] = {}
        self._active_wp: dict[str, str] = {}  # monitor -> wallpaper title

        # --- Main layout ---
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root_box)

        # Header
        header = Adw.HeaderBar()
        root_box.append(header)

        # Scrolled flowbox
        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        root_box.append(scrolled)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(10)
        self.flowbox.set_min_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_column_spacing(8)
        self.flowbox.set_row_spacing(8)
        self.flowbox.set_margin_start(8)
        self.flowbox.set_margin_end(8)
        self.flowbox.set_margin_top(8)
        self.flowbox.set_margin_bottom(8)
        scrolled.set_child(self.flowbox)

        # --- Bottom action bar ---
        action_bar = Gtk.ActionBar()
        root_box.append(action_bar)

        # Monitor checkboxes
        mon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.chk_dp1 = Gtk.CheckButton(label="DP-1")
        self.chk_dp1.set_active(True)
        self.chk_hdmi = Gtk.CheckButton(label="HDMI-A-1")
        self.chk_hdmi.set_active(True)
        mon_box.append(self.chk_dp1)
        mon_box.append(self.chk_hdmi)
        action_bar.pack_start(mon_box)

        # FPS
        fps_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        fps_box.append(Gtk.Label(label="FPS"))
        self.spin_fps = Gtk.SpinButton.new_with_range(10, 240, 5)
        self.spin_fps.set_value(60)
        fps_box.append(self.spin_fps)
        action_bar.pack_start(fps_box)

        # Silent
        self.chk_silent = Gtk.CheckButton(label="Silent")
        self.chk_silent.set_active(True)
        action_bar.pack_start(self.chk_silent)

        # Apply / Stop buttons
        btn_apply = Gtk.Button(label="Apply")
        btn_apply.add_css_class("suggested-action")
        btn_apply.connect("clicked", self._on_apply)
        action_bar.pack_end(btn_apply)

        btn_stop = Gtk.Button(label="Stop")
        btn_stop.add_css_class("destructive-action")
        btn_stop.connect("clicked", self._on_stop)
        action_bar.pack_end(btn_stop)

        # Status label
        self.status_label = Gtk.Label(label="No wallpaper active")
        self.status_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.status_label.set_max_width_chars(50)
        action_bar.pack_end(self.status_label)

        # --- Load wallpapers ---
        self._wallpapers = discover_wallpapers()
        self._cards: list[WallpaperCard] = []
        for info in self._wallpapers:
            card = WallpaperCard(info)
            self._cards.append(card)
            self.flowbox.append(card)

        # Progressive thumbnail loading
        self._thumb_index = 0
        if self._cards:
            GLib.idle_add(self._load_thumb_batch)

    # -- Progressive loading --------------------------------------------------
    def _load_thumb_batch(self) -> bool:
        batch = 5
        for _ in range(batch):
            if self._thumb_index >= len(self._cards):
                return GLib.SOURCE_REMOVE
            self._cards[self._thumb_index].load_thumbnail()
            self._thumb_index += 1
        return GLib.SOURCE_CONTINUE

    # -- Actions --------------------------------------------------------------
    def _selected_info(self) -> WallpaperInfo | None:
        child = self.flowbox.get_selected_children()
        if not child:
            return None
        card = child[0].get_child()
        if isinstance(card, WallpaperCard):
            return card.info
        return None

    def _kill_monitor(self, monitor: str):
        """Kill the wallpaper process for a specific monitor."""
        proc = self._processes.pop(monitor, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._active_wp.pop(monitor, None)

    def _kill_all(self):
        """Kill all managed wallpaper processes."""
        for mon in list(self._processes):
            self._kill_monitor(mon)

    def _update_status(self):
        if not self._active_wp:
            self.status_label.set_text("No wallpaper active")
            return
        parts = [f"{name} [{mon}]" for mon, name in self._active_wp.items()]
        self.status_label.set_text("  |  ".join(parts))

    def _on_apply(self, _btn):
        info = self._selected_info()
        if info is None:
            self.status_label.set_text("Select a wallpaper first")
            return

        screens = []
        if self.chk_dp1.get_active():
            screens.append("DP-1")
        if self.chk_hdmi.get_active():
            screens.append("HDMI-A-1")
        if not screens:
            self.status_label.set_text("Select at least one monitor")
            return

        fps = int(self.spin_fps.get_value())

        # Launch one process per selected monitor, killing only those
        for scr in screens:
            self._kill_monitor(scr)

            cmd = [WE_BIN, "--fps", str(fps), "--no-fullscreen-pause"]
            if self.chk_silent.get_active():
                cmd.append("--silent")
            cmd += ["--screen-root", scr]
            cmd.append(str(WORKSHOP_DIR / info.workshop_id))

            try:
                self._processes[scr] = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self._active_wp[scr] = info.title
            except FileNotFoundError:
                self.status_label.set_text(f"{WE_BIN} not found")
                return

        self._update_status()

    def _on_stop(self, _btn):
        self._kill_all()
        self._update_status()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class WallpaperSelectorApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.wallpaper-selector",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        style = Adw.StyleManager.get_default()
        style.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        css = Gtk.CssProvider()
        css.load_from_string(
            """
            .badge {
                background: rgba(0,0,0,0.65);
                color: white;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        win = WallpaperSelectorWindow(self)
        win.present()


def main():
    app = WallpaperSelectorApp()
    app.run()


if __name__ == "__main__":
    main()
