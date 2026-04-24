from typing import Annotated

import typer
from typer import Option

from .widget import OBS_Dash_Widget

app = typer.Typer()


@app.command(help='run obs-dash')
def run(
    host: Annotated[str, Option('--host', '-h', help='OBS websocket host')] = 'localhost',
    port: Annotated[int, Option('--port', '-p', help='OBS websocket port',)] = 4455,
    preview: Annotated[bool, Option(help='Enable source video preview window')] = True,
    preview_width: Annotated[int, Option(help='Preview window width')] = 114,
    preview_height: Annotated[int, Option(help='Preview window height')] = 48,
    preview_interval: Annotated[float, Option(help='Preview snapshot sampling interval')] = 0.2,
) -> None:
    # widget
    widget = OBS_Dash_Widget(
        host,
        port,
        preview,
        preview_width,
        preview_height,
        preview_interval,
    )
    # call the run function from Gtk.Application
    widget.run(None)
