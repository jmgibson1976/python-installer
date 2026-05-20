# python-installer

A Laravel-inspired Python CLI tool that interactively scaffolds new Python projects. Answer a short
wizard of prompts and get a fully structured project with `pyproject.toml`, source skeleton, tests,
optional Docker configuration, database layer, and git initialisation — ready to code.

The wizard generates a fully wired project including:
- `pyproject.toml` with all selected dependencies
- `src/<pkg>/` source package with `__init__.py`, optional `__main__.py` (CLI), `env.py`, `config.py`, and `logging.py`
- `configs/settings.toml` — structured config auto-discovered at startup
- `.env` + `.env.example` — pre-populated with every env var the project uses
- `tests/` skeleton (pytest and/or unittest stubs based on selections)
- `README.md`, `.gitignore`, and `docs/` reference pages
- Docker: `docker-compose.yml` + `docker/runtimes/3.13/Dockerfile` (when Docker selected)
- Database: `src/<pkg>/database.py`, migrations, seeders, and `scripts/` (when a DB driver is selected)
- AI assistant: `.github/` Copilot workspace files + `docs/copilot.md` (when AI setup is enabled)

---

## Requirements

- Python `>=3.13`
- `git` (optional — only needed if you choose git initialisation during the wizard)

---

## Installation

### Standard install

```bash
git clone https://github.com/jmgibson1976/python-installer.git
cd python-installer
pip install -e .
cp .env.example .env
```

### Install in a virtual environment (recommended)

```bash
git clone https://github.com/jmgibson1976/python-installer.git
cd python-installer
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

---

## Usage

```bash
# Create a new project in the current directory
installer new

# Pass the project name directly (skips the name prompt)
installer new my-app

# Create the project in a specific directory
installer new my-app --path ~/Projects

# Use a relative or absolute path as the project name
installer new ../my-app
installer new /Users/me/Projects/my-app
```

### Wizard prompts

| Prompt | Default | Notes |
|---|---|---|
| Project name | — | Letters, numbers, dashes, underscores, periods |
| Version | `0.0.1` | |
| Initialize git? | Yes | |
| Set up AI assistant (Copilot)? | Yes | Adds `.github/` workspace files |
| Project runtime | `venv` | `venv`, `docker`, or `none` |
| Database driver | `none` | sqlite3, MySQL, MariaDB, PostgreSQL, MSSQL, Oracle, MongoDB |
| Database abstraction | `none` | SQLAlchemy ORM, `databases` (async) |
| Testing frameworks | `pytest` | pytest, unittest, hypothesis, Robot Framework, Selenium, Playwright, mock, testcontainers |
| Enable logging? | Yes | Adds `logging.py` + Rich console handler |
| Environment parsing | `dotenv` | `python-dotenv`, `dynaconf`, or none |
| CLI support | `none` | Typer, argparse, or none |
| Pre-commit hooks | — | `black`, `ruff`, `flake8`, `isort`, `mypy`, `pyupgrade`, `bandit`, `detect-secrets` (selects hooks; `pre-commit` is auto-added as a dev dep) |

---

## What gets generated

### Always

```
<project-name>/
├── src/<pkg>/
│   └── __init__.py
├── README.md
└── pyproject.toml
```

### Conditional

| Selection | Generated files |
|---|---|
| `git=yes` | `.gitignore` |
| `env_parsing=dotenv\|dynaconf` | `.env`, `.env.example`, `src/<pkg>/env.py`, `src/<pkg>/config.py`, `configs/settings.toml` |
| `logging=yes` | `src/<pkg>/logging.py`, `logs/` directory |
| `docker=docker` | `docker-compose.yml`, `docker/runtimes/3.13/Dockerfile` |
| `cli_support=typer\|argparse` | `src/<pkg>/__main__.py`, `src/<pkg>/commands/hello.py`, `docs/cli.md` |
| `testing_frameworks` (any) | `tests/__init__.py` |
| `testing_frameworks` includes `pytest` | `tests/test_sample.py` |
| `testing_frameworks` includes `unittest` | `tests/test_sample_unittest.py` |
| `db_driver` (any SQL) | `src/<pkg>/database.py`, `docs/database.md`, `database/migrations/`, `database/seeders/`, `scripts/migrate.sh`, `scripts/rollback.sh`, `scripts/refresh.sh`, `scripts/seed.sh` |
| `db_driver=nosql` | `src/<pkg>/database.py`, `docs/database.md`, `database/README.md` |
| `ai_setup=yes` | `.github/copilot-instructions.md`, `.github/instructions/python.instructions.md`, conditional instruction files, `.github/skills/run-tests/SKILL.md`, `.github/agents/feature-planner.agent.md`, `.github/hooks/hooks.json`, `docs/copilot.md` |
| `ai_setup=yes` + `git=yes` | `.github/hooks/pre-commit`, `.github/prompts/new-feature.prompt.md`, `.github/prompts/plan-feature.prompt.md` |

---

## Running tests

```bash
python3 -m pytest
```

---

## Docker

Generated projects that include Docker support use `python:3.13-alpine` as their base image.
Alpine is minimal and has a near-zero CVE surface, but it uses `musl libc` instead of `glibc`.
Some packages with C extensions require extra build dependencies — add them to the generated
`Dockerfile` before your `pip install` step:

```dockerfile
# Common build deps for packages with C extensions
RUN apk add --no-cache gcc musl-dev

# Database-specific extras
RUN apk add --no-cache libpq-dev      # psycopg2 (PostgreSQL)
RUN apk add --no-cache mariadb-dev    # mysqlclient / PyMySQL (MySQL/MariaDB)
RUN apk add --no-cache unixodbc-dev   # pyodbc (MSSQL)
```

---

## Project structure (installer source)

```
installer/
  __main__.py              ← entry point; registers the Typer app
  commands/
    new.py                 ← `installer new` command
  prompts/
    definitions.py         ← PromptDef dataclass + PROMPTS registry
    runner.py              ← runs wizard prompts, persists state to temp JSON
  generator/
    scaffold.py            ← creates directory tree, calls toml_builder + stubs
    toml_builder.py        ← maps Answers → deps, renders pyproject.toml
    stubs.py               ← renders Jinja2 templates into the new project
  models/
    answers.py             ← Answers dataclass (single source of truth)
  stubs/                   ← Jinja2 (.j2) templates and static files
    README.md.j2
    __init__.py.j2
    .gitignore.j2
    .env.example.j2
    env.py.j2
    config.py.j2
    logging.py.j2
    database.py.j2
    configs/settings.toml.j2
    cli/                   ← __main__.py, commands/, docs.md
    docker/                ← Dockerfile, docker-compose.yml
    database/              ← docs.md, migrations/, seeders/
    scripts/               ← migrate.sh, rollback.sh, refresh.sh, seed.sh
    docs/copilot.md.j2
    github/                ← copilot-instructions.md, instructions/, skills/, agents/, hooks/, prompts/
    tests/                 ← test_sample.py, test_sample_unittest.py

tests/                     ← pytest suite mirroring installer/
```

---

## License

MIT

