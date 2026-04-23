# For GTK4 Layer Shell to get linked before libwayland-client we must explicitly load it before importing with gi
# ref: https://github.com/wmww/gtk4-layer-shell/blob/main/examples/simple-example.py
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
    def __init__(
        self,
        host: str,
        port: int,
        preview: bool,
        preview_width: int,
        preview_height: int,
    ) -> None:
        super().__init__()
        # attrs
        self._preview = preview
        # client
        self._client = OBS_Client(
            host,
            port,
            preview,
            preview_width,
            preview_height,
            set_text=self.set_text,
            set_css_classes=self.set_css_classes,
            set_preview_image=self.set_preview_image,
        )
        # UI components
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._timer_label = Gtk.Label(label='00:00:00')
        self._preview_picture = Gtk.Picture()
        self._preview_picture.set_size_request(preview_width, preview_height)

    def do_activate(self) -> None:
        # Create a window
        win = Gtk.ApplicationWindow(application=self)

        # Initialize Layer Shell
        LayerShell.init_for_window(win)

        # Set Layer (Top means above normal windows, Overlay means above everything)
        LayerShell.set_layer(win, LayerShell.Layer.OVERLAY)

        # Position the widget (Top Right corner)
        LayerShell.set_anchor(win, LayerShell.Edge.TOP, True)
        LayerShell.set_anchor(win, LayerShell.Edge.RIGHT, True)
        LayerShell.set_margin(win, LayerShell.Edge.TOP, 20)
        LayerShell.set_margin(win, LayerShell.Edge.RIGHT, 20)

        # Add Conditional Preview Widget
        if self._preview:
            self._box.append(self._preview_picture)

        # Add Timer Label
        self._timer_label.set_halign(Gtk.Align.CENTER)
        self._timer_label.set_valign(Gtk.Align.CENTER)
        self._box.append(self._timer_label)

        # Styling UI components via CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS, -1)
        Gtk.StyleContext.add_provider_for_display(
            win.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )

        # Add box to window
        win.set_child(self._box)
        win.present()

        # CRITICAL: Force mouse passthrough for the entire screen. This must happen after win.present()
        # Create an empty cairo region and assign
        # In GTK4 Python, Gdk.surface.set_input_region takes a cairo.Region
        if (native := win.get_native()) is not None and (surface := native.get_surface()) is not None:
            empty_region = cairo.Region()
            surface.set_input_region(empty_region)

        # launch the client
        self._client.run()

    def set_text(self, text: str) -> None:
        def callback(text: str) -> bool:
            self._timer_label.set_text(text)
            return False  # Required for idle_add one-shot calls
        GLib.idle_add(callback, text)

    def set_css_classes(self, *names: str) -> None:
        def callback(*names: str) -> bool:
            self._box.set_css_classes(*names)
            return False
        GLib.idle_add(callback, names)

    def set_preview_image(self, image: bytes | None) -> None:
        def callback(image: bytes | None) -> bool:
            # return when preview is disabled
            if not self._preview:
                return False
            # return when ping failed
            if image is None:
                self._preview_picture.set_paintable(None)
                return False
            # make new texture from the bytes
            gbytes = GLib.Bytes.new(image)
            texture = Gdk.Texture.new_from_bytes(gbytes)
            # paint the texture
            self._preview_picture.set_paintable(texture)
            return False
        GLib.idle_add(callback, image)
