from __future__ import annotations

import subprocess
from pathlib import Path

from installer.generator.stubs import render_stubs
from installer.generator.toml_builder import render_toml
from installer.models.answers import Answers


def create_project(answers: Answers) -> Path:
    """
    Build the full project directory structure from the collected answers.

    Returns the path to the created project root.
    """
    project_root = Path(answers.target_path)
    pkg_name = answers.project_name.replace("-", "_")

    # ── Directory tree ────────────────────────────────────────────────────────
    src_pkg = project_root / "src" / pkg_name
    src_pkg.mkdir(parents=True, exist_ok=True)
    (project_root / "tests").mkdir(exist_ok=True)

    # ── Source package skeleton ───────────────────────────────────────────────
    _write(src_pkg / "__init__.py", f'"""{ answers.project_name } package."""\n')
    _write(src_pkg / "__main__.py", _main_stub(pkg_name, answers))
    _write(project_root / "tests" / "__init__.py", "")
    _write(project_root / "tests" / f"test_{pkg_name}.py", _test_stub(pkg_name))

    # ── pyproject.toml ────────────────────────────────────────────────────────
    _write(project_root / "pyproject.toml", render_toml(answers))

    # ── .env.example (if env parsing enabled) ────────────────────────────────
    if answers.env_parsing != "none":
        _write(project_root / ".env.example", "# Add environment variables here\n")
        _write(project_root / ".env", "# Local overrides — do not commit\n")

    # ── Stubs (README, .gitignore, Dockerfile, etc.) ─────────────────────────
    render_stubs(answers, project_root)

    # ── Git init ──────────────────────────────────────────────────────────────
    if answers.git:
        _git_init(project_root)

    return project_root


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _main_stub(pkg_name: str, answers: Answers) -> str:
    lines = ['def main() -> None:']

    if answers.logging:
        lines = [
            "import logging",
            "",
            'logging.basicConfig(level=logging.INFO)',
            'logger = logging.getLogger(__name__)',
            "",
            "def main() -> None:",
            '    logger.info("Starting %s", __name__)',
        ]
    else:
        lines = [
            "def main() -> None:",
            f'    print("Hello from {pkg_name}!")',
        ]

    lines += [
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
    ]
    return "\n".join(lines) + "\n"


def _test_stub(pkg_name: str) -> str:
    return f"""\
def test_{pkg_name}_placeholder() -> None:
    \"\"\"Placeholder test — replace with real tests.\"\"\"
    assert True
"""


def _git_init(project_root: Path) -> None:
    try:
        subprocess.run(
            ["git", "init", "-b", "main", str(project_root)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(project_root), "add", "."],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "commit",
                "-m",
                "chore: initial project scaffold",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pass  # git not available or fails silently — project files are still created
