from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def _validate_project_name(value: str) -> bool | str:
    """Validate that the project name contains only allowed characters."""
    if not value.strip():
        return "Project name is required."
    if not re.match(r"^[a-zA-Z0-9._-]+$", value.strip()):
        return "May only contain letters, numbers, dashes, underscores, and periods."
    return True


def _validate_version(value: str) -> bool | str:
    if not value.strip():
        return "Version is required."
    return True


@dataclass
class PromptDef:
    """Definition of a single wizard prompt."""

    key: str
    prompt_type: str  # "text" | "confirm" | "select" | "checkbox"
    message: str
    default: Any = None
    choices: list[str] = field(default_factory=list)
    placeholder: str = ""
    required: bool = False
    validate: Any = None  # callable(str) -> bool | str


# ── Prompt registry (ordered) ─────────────────────────────────────────────────

PROMPTS: list[PromptDef] = [
    PromptDef(
        key="project_name",
        prompt_type="text",
        message="What is the name of your project?",
        placeholder="e.g. example-app",
        required=True,
        validate=_validate_project_name,
    ),
    PromptDef(
        key="version",
        prompt_type="text",
        message="Version",
        default="0.0.1",
        validate=_validate_version,
    ),
    PromptDef(
        key="git",
        prompt_type="confirm",
        message="Initialize a git repository?",
        default=True,
        required=True,
    ),
    PromptDef(
        key="docker",
        prompt_type="confirm",
        message="Should it run inside Docker?",
        default=False,
        required=True,
    ),
    PromptDef(
        key="db_driver",
        prompt_type="select",
        message="Which database driver will your application use?",
        default="none",
        choices=[
            "none",
            "sqlite",
            "mysql",
            "mariadb",
            "postgresql",
            "mssql",
            "oracle",
            "nosql",
        ],
    ),
    PromptDef(
        key="db_abstraction",
        prompt_type="select",
        message="Which database abstraction layer would you like?",
        default="none",
        choices=["none", "sqlalchemy", "databases"],
    ),
    PromptDef(
        key="testing_frameworks",
        prompt_type="checkbox",
        message="Which testing framework(s) would you like to add?",
        default=["pytest"],
        choices=[
            "pytest",
            "unittest",
            "hypothesis",
            "robotframework",
            "selenium",
            "playwright",
            "mock",
            "testcontainers",
        ],
    ),
    PromptDef(
        key="logging",
        prompt_type="confirm",
        message="Enable logging?",
        default=True,
        required=True,
    ),
    PromptDef(
        key="env_parsing",
        prompt_type="select",
        message="Which environment variable parsing library would you like?",
        default="dotenv",
        choices=["none", "dotenv", "dynaconf"],
    ),
    PromptDef(
        key="cli_support",
        prompt_type="select",
        message="Which CLI support library would you like?",
        default="none",
        choices=["none", "typer", "argparse"],
    ),
    PromptDef(
        key="optional_deps",
        prompt_type="checkbox",
        message="Which optional dev dependencies would you like?",
        default=[],
        choices=["pre-commit", "ruff", "black", "detect-secrets"],
    ),
]


def get_prompt(key: str) -> PromptDef | None:
    return next((p for p in PROMPTS if p.key == key), None)
