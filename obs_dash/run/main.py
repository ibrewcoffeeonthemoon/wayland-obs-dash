from typing import Annotated

import typer
from typer import Option

from .widget import OBS_Dash_Widget

app = typer.Typer()


@app.command(help='run obs-dash')
def run(
    host: Annotated[str, Option('--host', '-h', help='OBS websocket host')] = 'localhost',
    port: Annotated[int, Option('--port', '-p', help='OBS websocket port',)] = 4455,
    preview: Annotated[bool, Option('--preview', help='Enable source video preview window')] = False,
) -> None:
    widget = OBS_Dash_Widget(host, port, preview)
    widget.run(None)
