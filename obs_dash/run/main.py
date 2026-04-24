import logging
from typing import Annotated

import typer
from typer import Option

from .args import Args
from .widget import OBS_Dash_Widget

app = typer.Typer()


@app.command(help='run obs-dash')
def run(
    host: Annotated[str, Option('--host', '-h', help='OBS websocket host')] = 'localhost',
    port: Annotated[int, Option('--port', '-p', help='OBS websocket port',)] = 4455,
    show_video: Annotated[bool, Option(help='Enable source video preview window')] = True,
    video_width: Annotated[int, Option(help='Preview window width')] = 114,
    video_height: Annotated[int, Option(help='Preview window height')] = 48,
    video_sampling_interval: Annotated[float, Option(help='Preview snapshot sampling interval')] = 0.2,
    debug: Annotated[bool, Option(help='Enable debug mode verbose output')] = False,
) -> None:
    # logger
    logging.basicConfig(
        level=logging.INFO if debug else logging.WARNING,
        format='%(levelname)s | %(filename)s:%(lineno)d | %(message)s'
    )

    # params
    args = Args(
        host,
        port,
        show_video,
        video_width,
        video_height,
        video_sampling_interval,
    )
    # widget
    widget = OBS_Dash_Widget(args)
    # call the run function from Gtk.Application
    widget.run(None)
