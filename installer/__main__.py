import typer

from dotenv import load_dotenv

app = typer.Typer(
    name="python-installer",
    help="Python-Installer: new python project installer",
    add_completion=False,
)

def main() -> None:
    load_dotenv()
    typer.echo("Welcome to Python-Installer!")


if __name__ == "__main__":
    main()