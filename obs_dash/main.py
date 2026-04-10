import importlib.metadata as meta

import typer

NAME = 'wayland-obs-dash'


app = typer.Typer(
    name=NAME,
    no_args_is_help=True,
    help='A obs-studio status monitor overlay tool for Wayland',
)


@app.command(help='show version info')
def version() -> None:
    print(f'v{meta.version(NAME)}')
