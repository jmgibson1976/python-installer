from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Optional

import questionary
from rich.console import Console

from installer.models.answers import Answers
from installer.prompts.definitions import PROMPTS, PromptDef

console = Console()

# Choice display labels (shown in prompts) → internal keys
_DB_DRIVER_LABELS: dict[str, str] = {
    "none": "None",
    "sqlite": "SQLite (sqlite3 — stdlib)",
    "mysql": "MySQL (pymysql)",
    "mariadb": "MariaDB (pymysql)",
    "postgresql": "PostgreSQL (psycopg2-binary)",
    "mssql": "MSSQL (pyodbc)",
    "oracle": "Oracle (python-oracledb)",
    "nosql": "NoSQL / MongoDB (pymongo)",
}

_DB_ABSTRACTION_LABELS: dict[str, str] = {
    "none": "None",
    "sqlalchemy": "SQLAlchemy (ORM)",
    "databases": "Databases (async multi-DB abstraction)",
}

_TESTING_LABELS: dict[str, str] = {
    "pytest": "PyTest",
    "unittest": "PyUnit (unittest — stdlib)",
    "hypothesis": "Hypothesis",
    "robotframework": "Robot Framework",
    "selenium": "Selenium",
    "playwright": "Playwright",
    "mock": "unittest.Mock (stdlib)",
    "testcontainers": "Testcontainers",
}

_ENV_LABELS: dict[str, str] = {
    "none": "None",
    "dotenv": "dotenv (python-dotenv)",
    "dynaconf": "Dynaconf",
}

_CLI_LABELS: dict[str, str] = {
    "none": "None",
    "typer": "Typer",
    "argparse": "ArgParser (stdlib)",
}

_OPT_DEP_LABELS: dict[str, str] = {
    "pre-commit": "pre-commit",
    "ruff": "ruff",
    "black": "black",
    "detect-secrets": "detect-secrets",
}

_DOCKER_LABELS: dict[str, str] = {
    "none": "None (no runtime environment)",
    "docker": "Docker",
    "venv": "Python virtual environment (venv)",
}

_CHOICE_LABELS: dict[str, dict[str, str]] = {
    "docker": _DOCKER_LABELS,
    "db_driver": _DB_DRIVER_LABELS,
    "db_abstraction": _DB_ABSTRACTION_LABELS,
    "testing_frameworks": _TESTING_LABELS,
    "env_parsing": _ENV_LABELS,
    "cli_support": _CLI_LABELS,
    "optional_deps": _OPT_DEP_LABELS,
}


def _label_for(key: str, value: str) -> str:
    labels = _CHOICE_LABELS.get(key, {})
    return labels.get(value, value)


def _key_for(key: str, label: str) -> str:
    labels = _CHOICE_LABELS.get(key, {})
    reverse = {v: k for k, v in labels.items()}
    return reverse.get(label, label)


def _ask(prompt: PromptDef, skip_name: bool = False, answers: Optional["Answers"] = None) -> Any:
    """Ask a single prompt and return the raw answer value (internal key)."""
    if prompt.key == "project_name" and skip_name:
        return None

    # Skip db_abstraction when no db driver selected
    if prompt.key == "db_abstraction" and answers is not None and answers.db_driver == "none":
        return "none"

    if prompt.prompt_type == "text":
        kwargs: dict[str, Any] = {
            "message": prompt.message,
        }
        if prompt.default is not None:
            kwargs["default"] = str(prompt.default)
        if prompt.placeholder:
            kwargs["instruction"] = f"({prompt.placeholder})"
        if prompt.validate:
            kwargs["validate"] = prompt.validate
        return questionary.text(**kwargs).ask()

    if prompt.prompt_type == "confirm":
        return questionary.confirm(
            message=prompt.message,
            default=bool(prompt.default),
            auto_enter=False,
        ).ask()

    if prompt.prompt_type == "select":
        labels = [_label_for(prompt.key, c) for c in prompt.choices]
        default_label = _label_for(prompt.key, str(prompt.default))
        answer_label = questionary.select(
            message=prompt.message,
            choices=labels,
            default=default_label,
        ).ask()
        return _key_for(prompt.key, answer_label)

    if prompt.prompt_type == "checkbox":
        default_keys = set(prompt.default or [])
        choices = [
            questionary.Choice(
                title=_label_for(prompt.key, c),
                value=c,
                checked=c in default_keys,
            )
            for c in prompt.choices
        ]
        answer_keys = questionary.checkbox(
            message=prompt.message,
            choices=choices,
        ).ask()
        return answer_keys or []

    raise ValueError(f"Unknown prompt type: {prompt.prompt_type!r}")


def run_prompts(
    answers: Answers,
    skip_name: bool = False,
    temp_path: Optional[Path] = None,
) -> Answers:
    """
    Run all prompts in order, update *answers* in place, and persist to a temp
    JSON file after each answer.  Returns the populated Answers instance.

    Args:
        answers: Pre-populated Answers (e.g. project_name set from CLI arg).
        skip_name: When True the project_name prompt is skipped.
        temp_path: Path to the temp JSON file; created if not supplied.
    """
    if temp_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".json", prefix="python_installer_")
        import os
        os.close(fd)
        temp_path = Path(tmp)

    # Persist initial state (name + target_path already set by caller)
    _persist(answers, temp_path)

    for prompt in PROMPTS:
        value = _ask(prompt, skip_name=skip_name, answers=answers)
        if value is None:
            continue  # skipped (name already provided)

        # mock (unittest.mock) is part of unittest — auto-add it when not already selected
        if prompt.key == "testing_frameworks" and isinstance(value, list):
            if "mock" in value and "unittest" not in value:
                value = ["unittest"] + value

        setattr(answers, prompt.key, value)
        _persist(answers, temp_path)

    return answers


def _persist(answers: Answers, path: Path) -> None:
    """Write answers to the temp JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(answers.to_dict(), fh, indent=2)
