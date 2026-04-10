import typer

from .overlay import overlay

app = typer.Typer()


@app.command(help='run obs-dash')
def run() -> None:
    overlay()
