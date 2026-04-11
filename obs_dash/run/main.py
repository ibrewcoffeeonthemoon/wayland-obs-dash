import typer

from .widget import OBSStatusWidget

app = typer.Typer()


@app.command(help='run obs-dash')
def run() -> None:
    widget = OBSStatusWidget()
    widget.run(None)
