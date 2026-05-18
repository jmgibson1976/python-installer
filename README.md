# python-installer

A Laravel-inspired Python CLI tool that interactively scaffolds new Python projects. Answer a short
wizard of prompts and get a fully structured project with `pyproject.toml`, source skeleton, tests,
optional Docker configuration, and git initialisation — ready to code.

The wizard generates a fully wired project including:
- `pyproject.toml` with all selected dependencies
- `src/<pkg>/` source package with `__init__.py`, `__main__.py`, and an optional `config.py`
- `configs/settings.toml` — structured config auto-discovered at startup
- `.env` + `.env.example` — pre-populated with every env var the project uses
- `configs/` — drop `.toml` files here; they are merged automatically into `settings`
- `tests/` skeleton
- `README.md` and `.gitignore`
- Docker: `docker-compose.yml` + `docker/runtimes/3.13/Dockerfile` (when docker selected)

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

The wizard will ask about:
- Project name & version
- Git initialisation
- Docker support
- Database driver & abstraction layer
- Testing frameworks
- Logging, environment parsing, CLI support
- Optional dev dependencies (ruff, black, pre-commit, detect-secrets)

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
  __main__.py        ← entry point
  commands/new.py    ← new command
  prompts/           ← wizard definitions & runner
  generator/         ← scaffold, toml builder, stub renderer
  models/answers.py  ← collected wizard answers
  stubs/             ← Jinja2 templates for generated projects
    README.md.j2
    .gitignore
    .env.example.j2
    config.py.j2
    configs/
      settings.toml.j2
    docker/
      docker-compose.yml.j2
      runtimes/3.13/Dockerfile.j2
tests/               ← pytest suite mirroring installer/
```

---

## License

MIT
