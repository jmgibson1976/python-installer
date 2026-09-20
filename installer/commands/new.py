from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from installer.generator.scaffold import create_project
from installer.models.answers import Answers
from installer.prompts.definitions import _validate_project_name
from installer.prompts.runner import WizardAborted, run_prompts

console = Console()

# The root of the installer's own source tree — used to guard against
# accidentally scaffolding inside it.
_INSTALLER_ROOT = Path(__file__).resolve().parents[2]


def _resolve_target(name: str, explicit_path: Optional[str]) -> tuple[str, str]:
    """
    Return ``(project_name, target_path)`` from the raw CLI inputs.

    Rules (in priority order):
    1. If *name* is absolute (e.g. ``/home/user/my-app``) — use it as-is.
    2. If *name* contains path separators (e.g. ``../my-app``) — resolve
       relative to CWD, use the final component as the project name.
    3. If ``--path`` was supplied — join it with *name*.
    4. Default: join CWD with *name*.
    """
    name_path = Path(name)

    if name_path.is_absolute():
        resolved = name_path.resolve()
        return resolved.name, str(resolved)

    if len(name_path.parts) > 1:
        base = Path.cwd() / name_path
        resolved = base.resolve()
        return resolved.name, str(resolved)

    base = Path(explicit_path).resolve() if explicit_path else Path.cwd()
    return name, str(base / name)


def _guard_installer_dir(target: Path) -> None:
    """Abort if the target would be created inside the installer's own tree."""
    try:
        target.relative_to(_INSTALLER_ROOT)
        console.print(
            "\n[bold red]Error:[/bold red] You are running this command from inside "
            "the python-installer source directory.\n"
            "Please run it from outside the project, or pass an explicit path:\n\n"
            f"  [bold]installer new my-app --path /your/desired/directory[/bold]\n"
        )
        raise typer.Exit(1)
    except ValueError:
        pass  # target is outside the installer tree — all good


def new(
    project_name: Optional[str] = typer.Argument(
        None,
        help=(
            "Name of the new project. May include a relative or absolute path prefix "
            "(e.g. '../my-app' or '/home/user/my-app'). Collected via prompt if omitted."
        ),
    ),
    path: Optional[str] = typer.Option(
        None,
        "--path",
        "-p",
        help="Base directory to create the project in. Defaults to current working directory.",
    ),
) -> None:
    """Scaffold a new Python project interactively."""
    _print_banner()
    console.print("  [dim]Press Ctrl+C at any time to exit.[/dim]\n")

    answers = Answers()

    # ── Early guard: check the base directory before asking anything ──────────
    # When no explicit path is given, any project will land under CWD (or the
    # --path dir). If that base is inside the installer tree, fail immediately.
    base = Path(path).resolve() if path else Path.cwd()
    _guard_installer_dir(base)

    if project_name:
        result = _validate_project_name(project_name.strip())
        if result is not True:
            console.print(f"[red]Invalid project name:[/red] {result}")
            raise typer.Exit(1)
        clean_name, target_path = _resolve_target(project_name.strip(), path)
        answers.project_name = clean_name
        answers.target_path = target_path
        _guard_installer_dir(Path(target_path))

    # ── Run interactive wizard ────────────────────────────────────────────────
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="python_installer_")
    os.close(fd)

    try:
        run_prompts(answers, skip_name=bool(project_name), temp_path=Path(tmp_path))

        # If name was collected via prompt, resolve target now
        if not project_name and answers.project_name:
            _, target_path = _resolve_target(answers.project_name, path)
            answers.target_path = target_path
            _guard_installer_dir(Path(target_path))

        if not answers.project_name:
            console.print("[red]Aborted: no project name provided.[/red]")
            raise typer.Exit(1)

        # ── Generate project ──────────────────────────────────────────────────
        console.print()
        with console.status("[bold green]Scaffolding your project…[/bold green]"):
            project_root = create_project(answers)

        _print_success(answers, project_root)

    except WizardAborted:
        console.print("\n[yellow]Wizard cancelled.[/yellow]")
        raise typer.Exit(0)

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _print_banner() -> None:
    title = Text("🐍 Python Installer", style="bold green")
    subtitle = Text("Python project scaffolding", style="dim")
    panel = Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="green",
        padding=(1, 4),
    )
    console.print(panel)
    console.print()


def _print_success(answers: Answers, project_root: Path) -> None:
    console.print()
    msg = Text.assemble(
        ("✔ ", "bold green"),
        ("Project ", ""),
        (answers.project_name, "bold cyan"),
        (" created at ", ""),
        (str(project_root), "bold white"),
    )
    console.print(Panel(msg, border_style="green", padding=(0, 2)))
    console.print()
    console.print("  [dim]Next steps:[/dim]")
    console.print(f"    [bold]cd {project_root}[/bold]")

    if answers.docker == "docker":
        console.print("    [bold]cp .env.example .env[/bold]")
        console.print("    [bold]docker compose up --build[/bold]")
    elif answers.docker == "venv":
        console.print("    [bold]python -m venv .venv[/bold]")
        console.print("    [bold]source .venv/bin/activate[/bold]  [dim]# Windows: .venv\\Scripts\\activate[/dim]")
        console.print("    [bold]pip install -e \".[dev]\"[/bold]")
        console.print("    [bold]python -m " + re.sub(r"[^a-zA-Z0-9_]", "_", answers.project_name) + "[/bold]")
    else:
        console.print("    [bold]pip install -e \".[dev]\"[/bold]")
        console.print("    [bold]python -m " + re.sub(r"[^a-zA-Z0-9_]", "_", answers.project_name) + "[/bold]")

    console.print()
