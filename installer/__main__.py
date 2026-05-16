import typer
from dotenv import load_dotenv

from installer.commands.new import new

app = typer.Typer(
    name="installer",
    help="Python-Installer: scaffold a new Python project.",
    add_completion=False,
)

app.command("new")(new)


@app.callback()
def _callback() -> None:
    """Python-Installer: scaffold a new Python project."""
    load_dotenv()


def main() -> None:
    app()


if __name__ == "__main__":
    main()