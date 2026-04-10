import typer

app = typer.Typer()


@app.command(help='run obs-dash')
def run(
) -> None:
    print('obs-dash run')
