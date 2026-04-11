# For GTK4 Layer Shell to get linked before libwayland-client we must explicitly load it before importing with gi
# ref: https://github.com/wmww/gtk4-layer-shell/blob/main/examples/simple-example.py
import threading
from ctypes import CDLL

import cairo
import gi

from .style import CSS
from .websocket import OBS_Client

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


class OBS_Dash_Widget(Gtk.Application):
    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self._client = OBS_Client(
            host,
            port,
            set_text=self.set_text,
            set_css_classes=self.set_css_classes,
        )
        # UI components
        self._label = Gtk.Label(label='00:00:00')
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

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
        self._label.set_halign(Gtk.Align.CENTER)
        self._label.set_valign(Gtk.Align.CENTER)

        # Container to act as the "Red Box"
        self._box.set_size_request(120, 50)
        self._box.append(self._label)

        # Styling the Red Box via CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS, -1)

        Gtk.StyleContext.add_provider_for_display(
            win.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        win.set_child(self._box)
        win.present()

        # launch the client
        self._client.run()

    def set_text(self, text: str) -> None:
        def callback(text: str) -> bool:
            self._label.set_text(text)
            return False  # Required for idle_add one-shot calls
        GLib.idle_add(callback, text)

    def set_css_classes(self, *names: str) -> None:
        def callback(*names: str) -> bool:
            self._box.set_css_classes(*names)
            return False
        GLib.idle_add(callback, names)
