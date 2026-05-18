from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from installer.models.answers import Answers

_STUBS_DIR = Path(__file__).parent.parent / "stubs"


def _jinja_env(stubs_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(stubs_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def _render_template(env: Environment, template_path: str, context: dict) -> str:
    return env.get_template(template_path).render(**context)


def _stub_context(answers: Answers) -> dict:
    return {
        "project_name": answers.project_name,
        "pkg_name": answers.project_name.replace("-", "_"),
        "version": answers.version,
        "db_driver": answers.db_driver,
        "db_abstraction": answers.db_abstraction,
        "testing_frameworks": answers.testing_frameworks,
        "logging_enabled": answers.logging,
        "env_parsing": answers.env_parsing,
        "cli_support": answers.cli_support,
        "docker": answers.docker,
    }


def render_stubs(answers: Answers, project_root: Path) -> None:
    """
    Render and write all applicable stub files into *project_root*.

    Always rendered:
      - README.md
      - .gitignore

    Conditionally rendered:
      - .env.example                          (when env_parsing != "none")
      - <pkg_name>/config.py                  (when env_parsing != "none")
      - configs/settings.toml                 (when env_parsing != "none")
      - docker/runtimes/3.13/Dockerfile  (when docker="docker")
      - docker-compose.yml               (when docker="docker")
    """
    env = _jinja_env(_STUBS_DIR)
    context = _stub_context(answers)

    _write(project_root / "README.md", _render_template(env, "README.md.j2", context))
    _write(project_root / ".gitignore", (_STUBS_DIR / ".gitignore").read_text())

    if answers.env_parsing != "none":
        pkg_name = answers.project_name.replace("-", "_")
        _write(project_root / ".env.example", _render_template(env, ".env.example.j2", context))
        _write(
            project_root / "src" / pkg_name / "config.py",
            _render_template(env, "config.py.j2", context),
        )
        _write(
            project_root / "configs" / "settings.toml",
            _render_template(env, "configs/settings.toml.j2", context),
        )

    if answers.docker == "docker":
        _write(
            project_root / "docker" / "runtimes" / "3.13" / "Dockerfile",
            _render_template(env, "docker/runtimes/3.13/Dockerfile.j2", context),
        )
        _write(
            project_root / "docker-compose.yml",
            _render_template(env, "docker/docker-compose.yml.j2", context),
        )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
