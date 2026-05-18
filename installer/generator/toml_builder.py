from __future__ import annotations

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
    "mock": [],             # stdlib
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

    dev.extend(answers.optional_deps)

    # Deduplicate while preserving order
    runtime = list(dict.fromkeys(runtime))
    dev = list(dict.fromkeys(dev))

    return runtime, dev


def render_toml(answers: Answers) -> str:
    """Render a ``pyproject.toml`` string from the collected answers."""
    runtime_deps, dev_deps = build_dependencies(answers)

    dep_lines = "\n".join(f'    "{dep}",' for dep in runtime_deps)
    dev_dep_lines = "\n".join(f'    "{dep}",' for dep in dev_deps)

    runtime_block = f"[\n{dep_lines}\n]" if dep_lines else "[]"
    dev_block = f"[\n{dev_dep_lines}\n]" if dev_dep_lines else "[]"

    pkg_name = answers.project_name.replace("-", "_")

    return f"""\
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{answers.project_name}"
version = "{answers.version}"
description = ""
readme = "README.md"
requires-python = ">=3.13"
dependencies = {runtime_block}

[project.optional-dependencies]
dev = {dev_block}

[tool.setuptools]
package-dir = {{"" = "src"}}

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
{pkg_name} = "{pkg_name}.__main__:main"
"""
