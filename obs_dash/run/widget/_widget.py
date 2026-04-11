# For GTK4 Layer Shell to get linked before libwayland-client we must explicitly load it before importing with gi
# ref: https://github.com/wmww/gtk4-layer-shell/blob/main/examples/simple-example.py
import threading
from ctypes import CDLL

import cairo
import gi

from .websocket import OBSClient

# pre-loading
CDLL('libgtk4-layer-shell.so')
# pre-checking
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')

# MUST load after CDLL("libgtk4-layer-shell.so") pre-loading
# should load after gi.require_version pre-checking
from gi.repository import Gdk, Gtk, GLib  # noqa
from gi.repository import Gtk4LayerShell as LayerShell  # noqa


class OBSStatusWidget(Gtk.Application):
    def __init__(self) -> None:
        super().__init__()
        self._client = OBSClient(
            update_label=self.update_label
        )

    def do_activate(self) -> None:
        # Create a window
        win = Gtk.ApplicationWindow(application=self)

        # 1. Initialize Layer Shell
        LayerShell.init_for_window(win)

        # 2. Set Layer (Top means above normal windows, Overlay means above everything)
        LayerShell.set_layer(win, LayerShell.Layer.OVERLAY)

        # 3. Position the widget (Top Right corner)
        LayerShell.set_anchor(win, LayerShell.Edge.TOP, True)
        LayerShell.set_anchor(win, LayerShell.Edge.RIGHT, True)
        LayerShell.set_margin(win, LayerShell.Edge.TOP, 20)
        LayerShell.set_margin(win, LayerShell.Edge.RIGHT, 20)

        # 4. UI Components
        self.label = Gtk.Label(label='00:00:00')
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)

        # Container to act as the "Red Box"
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(120, 50)
        box.append(self.label)

        # Styling the Red Box via CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data('''
            box {
                background-color: #ff0000;
                border-radius: 12px;
                padding: 10px; /* Gives the text some breathing room */
            }
            label {
                color: white;
                font-weight: 800; /* Extra bold */
                font-size: 32px;  /* Much larger text */
            }
        ''', -1)

        Gtk.StyleContext.add_provider_for_display(
            win.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        win.set_child(box)
        win.present()

        # worker thread
        t = threading.Thread(target=self._client.run, daemon=True)
        t.start()

    def update_label(self, text: str) -> None:
        def callback(text: str) -> bool:
            self.label.set_text(text)
            return False  # Required for idle_add one-shot calls
        GLib.idle_add(callback, text)
