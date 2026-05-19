from __future__ import annotations

import re

from installer.models.answers import Answers

# ── Package mappings ──────────────────────────────────────────────────────────

_DB_DRIVER_PACKAGES: dict[str, list[str]] = {
    "none": [],
    "sqlite": [],           # stdlib
    "mysql": ["pymysql"],
    "mariadb": ["pymysql"],
    "postgresql": ["psycopg2-binary"],
    "mssql": ["pyodbc"],
    "oracle": ["python-oracledb"],
    "nosql": ["pymongo"],
}

_DB_ABSTRACTION_PACKAGES: dict[str, list[str]] = {
    "none": [],
    "sqlalchemy": ["sqlalchemy"],
    "databases": ["databases"],
}

_TESTING_PACKAGES: dict[str, list[str]] = {
    "pytest": ["pytest"],
    "unittest": [],         # stdlib
    "hypothesis": ["hypothesis"],
    "robotframework": ["robotframework"],
    "selenium": ["selenium"],
    "playwright": ["playwright"],
    "mock": [],             # stdlib (unittest.mock)
    "testcontainers": ["testcontainers"],
}

_ENV_PACKAGES: dict[str, list[str]] = {
    "none": [],
    "dotenv": ["python-dotenv"],
    "dynaconf": ["dynaconf"],
}

_CLI_PACKAGES: dict[str, list[str]] = {
    "none": [],
    "typer": ["typer"],
    "argparse": [],         # stdlib
}

_OPTIONAL_DEV_PACKAGES: dict[str, list[str]] = {
    "black": ["black"],
    "ruff": ["ruff"],
    "flake8": ["flake8"],
    "isort": ["isort"],
    "mypy": ["mypy"],
    "pyupgrade": [],        # pre-commit hook only — no pip install needed
    "bandit": ["bandit"],
    "detect-secrets": ["detect-secrets"],
}

# ── Stdlib display names (for TOML comments) ──────────────────────────────────
# Maps internal key → human-readable stdlib module name shown in comments.

_RUNTIME_STDLIB: dict[str, str] = {
    "sqlite": "sqlite3",
    "argparse": "argparse",
}

_DEV_STDLIB: dict[str, str] = {
    "unittest": "unittest",
    "mock": "unittest.mock",
}


def build_stdlib_notes(answers: Answers) -> tuple[list[str], list[str]]:
    """Return ``(runtime_stdlib, dev_stdlib)`` display names for stdlib choices."""
    runtime: list[str] = []
    dev: list[str] = []

    if answers.db_driver in _RUNTIME_STDLIB:
        runtime.append(_RUNTIME_STDLIB[answers.db_driver])
    if answers.cli_support in _RUNTIME_STDLIB:
        runtime.append(_RUNTIME_STDLIB[answers.cli_support])

    for fw in answers.testing_frameworks:
        if fw in _DEV_STDLIB:
            dev.append(_DEV_STDLIB[fw])

    return runtime, dev


def build_dependencies(answers: Answers) -> tuple[list[str], list[str]]:
    """
    Return ``(runtime_deps, dev_deps)`` derived from the wizard answers.

    Runtime deps go into ``[project] dependencies``.
    Dev deps go into ``[project.optional-dependencies] dev``.
    """
    runtime: list[str] = []
    dev: list[str] = []

    runtime.extend(_DB_DRIVER_PACKAGES.get(answers.db_driver, []))
    runtime.extend(_DB_ABSTRACTION_PACKAGES.get(answers.db_abstraction, []))
    runtime.extend(_ENV_PACKAGES.get(answers.env_parsing, []))
    runtime.extend(_CLI_PACKAGES.get(answers.cli_support, []))

    if answers.logging:
        runtime.extend(["rich", "python-dotenv"])

    for fw in answers.testing_frameworks:
        dev.extend(_TESTING_PACKAGES.get(fw, []))

    for tool in answers.optional_deps:
        dev.extend(_OPTIONAL_DEV_PACKAGES.get(tool, []))

    if answers.optional_deps:
        dev.append("pre-commit")

    # Deduplicate while preserving order
    runtime = list(dict.fromkeys(runtime))
    dev = list(dict.fromkeys(dev))

    return runtime, dev


def render_toml(answers: Answers) -> str:
    """Render a ``pyproject.toml`` string from the collected answers."""
    runtime_deps, dev_deps = build_dependencies(answers)
    runtime_stdlib, dev_stdlib = build_stdlib_notes(answers)

    dep_lines = "\n".join(f'    "{dep}",' for dep in runtime_deps)
    dev_dep_lines = "\n".join(f'    "{dep}",' for dep in dev_deps)

    runtime_block = f"[\n{dep_lines}\n]" if dep_lines else "[]"
    dev_block = f"[\n{dev_dep_lines}\n]" if dev_dep_lines else "[]"

    runtime_stdlib_comment = (
        f"# stdlib (no install needed): {', '.join(runtime_stdlib)}\n"
        if runtime_stdlib else ""
    )
    dev_stdlib_comment = (
        f"# stdlib (no install needed): {', '.join(dev_stdlib)}\n"
        if dev_stdlib else ""
    )

    pkg_name = re.sub(r"[^a-zA-Z0-9_]", "_", answers.project_name)

    toml = f"""\
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{answers.project_name}"
version = "{answers.version}"
description = ""
readme = "README.md"
requires-python = ">=3.13"
{runtime_stdlib_comment}dependencies = {runtime_block}

[project.optional-dependencies]
{dev_stdlib_comment}dev = {dev_block}

[tool.setuptools]
package-dir = {{"" = "src"}}

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
{pkg_name} = "{pkg_name}.__main__:main"
"""

    if "black" in answers.optional_deps:
        toml += """\

[tool.black]
line-length = 120
target-version = ["py313"]
"""

    if "isort" in answers.optional_deps:
        toml += """\

[tool.isort]
profile = "black"
line_length = 120
"""

    if "mypy" in answers.optional_deps:
        toml += """\

[tool.mypy]
ignore_missing_imports = true
python_version = "3.13"
"""

    return toml
