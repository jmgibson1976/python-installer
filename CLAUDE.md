# python-installer — CLAUDE.md

## Project Overview

`python-installer` is a Python CLI tool that interactively scaffolds new Python projects. It
collects user preferences via a wizard, then generates a complete project tree with `pyproject.toml`,
stubs, and optional Docker/git initialisation.

---

## Project Structure

```
installer/
  __main__.py              ← Entry point; registers the Typer app + `new` command via @app.callback()
  commands/
    new.py                 ← `installer new` command — path resolution, wizard orchestration, output
  prompts/
    definitions.py         ← PromptDef dataclass + ordered PROMPTS list + validators
    runner.py              ← Runs prompts with questionary, persists state to temp JSON, returns Answers
  generator/
    scaffold.py            ← Creates project directory tree; calls toml_builder + stubs; runs git init
    toml_builder.py        ← Maps Answers → runtime/dev deps; renders pyproject.toml string
    stubs.py               ← Renders Jinja2 stub templates conditionally based on Answers
  models/
    answers.py             ← Answers dataclass — single source of truth for all wizard answers
  stubs/                   ← Jinja2 (.j2) templates copied into new projects
    README.md.j2           ← Always rendered; conditionally includes docker/venv setup sections
    .gitignore.j2          ← Rendered when git=True; excludes logs/ when logging enabled
    .env.example.j2        ← Rendered when env_parsing != "none"; documents every env var
    __init__.py.j2         ← Always rendered; path constants, START_TIME, optional logging bootstrap
    env.py.j2              ← Rendered when env_parsing=="dotenv" or logging=True; cached env reader
    config.py.j2           ← Rendered when env_parsing != "none"; Settings/LazySettings wrapper
    logging.py.j2          ← Rendered when logging=True; configurable file+console logger
    configs/
      settings.toml.j2     ← Rendered when env_parsing != "none"; dynaconf TOML with @format env refs
    docker/
      docker-compose.yml.j2
      runtimes/
        3.13/
          Dockerfile.j2
    cli/                   ← Rendered when cli_support != "none"
      __main__.py.j2       ← Entry point; typer and argparse branches
      docs.md.j2           ← Rendered to docs/cli.md; usage guide + howto
      commands/
        __init__.py.j2     ← Empty package marker
        hello.py.j2        ← Sample command; typer and argparse branches

tests/                     ← Mirrors installer/ structure; pytest only
  commands/test_new.py
  prompts/test_definitions.py
  prompts/test_runner.py
  generator/test_scaffold.py
  generator/test_toml_builder.py
  generator/test_stubs.py
```

---

## Tech Stack & Dependencies

| Package | Role |
|---|---|
| `typer>=0.25.0` | CLI framework — argument/option parsing, app registration |
| `rich>=13.0` | Terminal colour, panels, spinners — all user-facing output |
| `questionary>=2.0` | Interactive prompts: text, confirm, select, checkbox |
| `jinja2>=3.0` | Stub template rendering |
| `python-dotenv>=1.0` | Loads `.env` for the installer itself at runtime |
| `pytest` | Test framework (dev dependency) |

**Python:** `>=3.13`
**Build backend:** `setuptools>=68`

---

## Architecture & Key Patterns

### Command registration

The app uses a `@app.callback()` in `__main__.py` to force Typer into multi-command mode (required
when there is only one command, otherwise Typer flattens the subcommand and breaks argument
parsing). Commands are registered with `app.command("name")(fn)` — decorators are **not** applied
in the command modules themselves.

### Wizard flow

1. `new` command resolves the target path via `_resolve_target()`, then calls `run_prompts()`
2. `run_prompts()` iterates `PROMPTS` in order, calls `_ask()` per prompt, and writes the full
   `Answers` state to a temp JSON file after every answer (session durability)
3. The temp file is always cleaned up in a `finally` block
4. `create_project()` orchestrates scaffold → toml → stubs → git init

### Path resolution (`_resolve_target`)

Priority order:
1. Absolute path in the name argument → used as-is
2. Relative path separators in the name (e.g. `../my-app`) → resolved from CWD
3. `--path` option supplied → `path / name`
4. Default → `CWD / name`

A `_guard_installer_dir()` check aborts with a helpful message if the resolved target falls inside
the installer's own source tree. If the resolved target path is inaccessible or invalid (e.g. a
parent directory does not exist or permissions are denied), abort with a clear error message
specifying the issue and suggest corrective actions to the user.

### Prompt definitions

Each prompt is a `PromptDef` dataclass with: `key`, `prompt_type`, `message`, `default`, `choices`,
`placeholder`, `required`, `validate`. The `PROMPTS` list in `definitions.py` is the single
authoritative registry — order matters (the wizard runs them sequentially).

### Checkbox prompts

`questionary.checkbox` does **not** accept a `default=` list of strings. Pre-checked items must be
expressed as `questionary.Choice(title=..., value=..., checked=True/False)` objects. Always use
this pattern for checkbox prompts.

### Conditional prompt skipping

`_ask()` receives the current `Answers` instance and may return early without showing a prompt.
Current skip rules:
- `project_name` prompt is skipped when the name was passed as a CLI argument
- `db_abstraction` prompt is skipped when `answers.db_driver == "none"`

Add new skip rules in `_ask()` by checking the relevant field on `answers` and returning the
appropriate default value, following the structure of the existing skip rules.

### Wizard input validation

Each prompt's `validate` callable returns `True` on success or an error string on failure.
`questionary` automatically re-prompts the user when a string is returned — do not re-implement
this loop manually.

`stubs.py` calls `jinja2.Environment(loader=FileSystemLoader(...), undefined=StrictUndefined)`.
`StrictUndefined` is intentional — it causes immediate errors for missing template variables
rather than silent empty strings. Always pass a complete context dict to `render_stubs()`.

### Config stub (`config.py` + `configs/`)

When `env_parsing != "none"`, `render_stubs()` generates:
- `src/<pkg>/config.py` — a `Settings` class (dotenv) or `LazySettings` wrapper (dynaconf)
- `configs/settings.toml` — seeded with an `[app]` section as a working example
- `.env.example` — documents every env var the project uses

**Critical rules for config stubs:**
- Never use `os.environ.get()` in generated code — read the root dir override from `.env` itself
  via `dotenv_values()` (avoids stale shell variable contamination).
- For dynaconf templates, use `@format {env[VAR_NAME]}` syntax in TOML so values delegate to
  the environment rather than being hardcoded.
- Every configurable value referenced in any stub **must** have a corresponding entry in
  `.env.example.j2`.

### env.py stub

`env.py.j2` is rendered when `env_parsing == "dotenv"` **or** `logging == True` (the
`needs_env_module` flag in `stubs.py`). It provides a single cached `.env` reader:
- `get_env(key, default=None)` — reads from a `dotenv_values()` cache; never from `os.environ`
- `reload_env()` — clears the cache so the next call re-reads `.env` from disk

All other stubs (`config.py`, `logging.py`) must import `get_env` from `<pkg>.env` rather than
calling `dotenv_values()` or `os.environ.get()` directly.

### Logging stub (`logging.py`)

Rendered when `logging == True`. Key design:
- `init()` — called once in `__init__.py`; sets up rotating file handler under `logs/` and
  optionally a Rich console handler (`LOG_CONSOLE=true` in `.env`)
- `get_logger(name)` — returns a named child logger; callers never call `logging.getLogger()` directly
- All settings (`LOG_LEVEL`, `LOG_RETENTION_DAYS`, `LOG_CONSOLE`) read via `get_env()`, never `os.environ`
- Log files are named `<name>-YYYY-MM-DD.log`; old files beyond `LOG_RETENTION_DAYS` are pruned on `init()`
- `logs/` directory is created at `ROOT_DIR / "logs"` (exported to `os.environ` in `__init__.py`)
- `logs/` must be added to `.gitignore.j2` when logging is enabled

### `__init__.py` stub

Always rendered. Responsibilities in order:
1. **`__version__`** — from `importlib.metadata.version()`; falls back to `"0.0.0"`.
   Never hardcode the version string here — `pyproject.toml` is the single source of truth.
2. **Path constants** — `ROOT_DIR`, `SRC_DIR`, and (when logging) `LOGS_DIR`, derived from `Path(__file__)`.
   Published to `os.environ` so sub-modules can find the project root without re-deriving it.
3. **`START_TIME`** — `datetime.now().isoformat()` written to `os.environ["<PKG>_START"]`.
4. **Logging bootstrap** (when `logging == True`) — imports and calls `_init_logging()`.
5. **Settings re-export** (when `env_parsing != "none"`) — `from <pkg>.config import settings`
   so callers can do `from <pkg> import settings`.

### Dependency mapping (toml_builder)

`build_dependencies(answers)` returns `(runtime_deps, dev_deps)`. Mapping dicts live at module
level (`_DB_DRIVER_PACKAGES`, etc.). When adding new prompt choices that carry dependencies, add
an entry to the appropriate mapping dict — do not compute deps inline in `render_toml()`.

### CLI stub (`__main__.py` + `commands/`)

Rendered when `cli_support != "none"`. Two variants share the same template files with Jinja2
conditional blocks:

**Typer variant:**
- `src/<pkg>/__main__.py` — `app = typer.Typer(...)`, `console = Console()`,
  `_version_callback()`, `@app.callback()` with `--version` (eager), `--verbose/-v`,
  `--debug/-d`. Commands registered as `app.command("<name>")(<fn>)`.
- `src/<pkg>/commands/hello.py` — typed `Argument`, `Option` with `min=`, `--upper/--no-upper`,
  debug panel dump, inline validation with `typer.BadParameter`.

**Argparse variant:**
- `src/<pkg>/__main__.py` — `App` class with `run()`; `ArgumentParser` with `--debug/-d`;
  `add_subparsers()`; dispatches to `<name>_command(args)` functions.
- `src/<pkg>/commands/hello.py` — `register(subparsers)` adds the subcommand definition;
  `hello_command(args: argparse.Namespace)` executes it.

**Debug mode (both variants):**
- Typer: `--debug/-d` flag on callback; commands print a Rich `Panel` of their kwargs.
- Argparse: `--debug` global flag OR `get_env("APP_DEBUG") == "true"` → prints `vars(args)`.
- `APP_DEBUG` is already in `.env.example` — no additional env var needed.

**Anti-patterns:**
- ❌ Do not read `APP_DEBUG` via `os.environ.get()` in generated argparse code — use `get_env()`
- ❌ Do not apply `@app.command()` decorators in command files — register from `__main__.py`

---

## Code Generation Guidelines

- Use `from __future__ import annotations` at the top of every module
- Use `pathlib.Path` for all filesystem paths — never `os.path`
- Use `logging` for diagnostics; use `rich` console for all user-facing CLI output — never raw `print()`
- Type-annotate all public functions; annotate non-trivial internal functions too
- Keep functions small and focused; orchestration logic belongs in `scaffold.py` / `new.py`
- Catch specific exceptions; never bare `except:` or silent `except ...: pass` without a comment
- Use f-strings for string interpolation
- Avoid mutable default arguments — use `field(default_factory=...)` in dataclasses

---

## Jinja2 Stub Rules

Every configurable value introduced in any stub template (`docker-compose.yml.j2`, `config.py.j2`,
`configs/settings.toml.j2`, etc.) **must** have a corresponding entry in `.env.example.j2`.

- If a new env var is referenced in any `.j2` template, add it to `.env.example.j2`.
- Never read configurable values from `os.environ` — use `dotenv_values()` to read from `.env` directly.
- For dynaconf templates, reference env vars using `@format {env[VAR_NAME]}` syntax.

All stub templates live under `installer/stubs/` and use the `.j2` extension. The Jinja2
environment uses `StrictUndefined` — every variable referenced in a template **must** be present
in the context dict. Missing variables raise `jinja2.UndefinedError` immediately.

Do not use Jinja2 control blocks or expressions for Docker `EXPOSE` port values that are not in
`Answers`. Use a hardcoded port instead. Docker language servers validate `.j2` files as
Dockerfiles and flag Jinja2 syntax as errors; add `# docker-language-server: ignore` as the
first comment line rather than removing valid Jinja2 syntax.

Before calling `render_stubs(answers, project_root)`, the `Answers` object must be fully
populated. When adding a new template variable, follow these steps **in order**:
1. Add the field to `Answers` in `models/answers.py`.
2. Add the key to the context dict in `stubs.py` inside `render_stubs()`.
3. Reference the key in the `.j2` template.

---

## Anti-Patterns to Avoid

### Command registration
- ❌ Do not apply `@app.command()` in command modules — register commands from `__main__.py`

### Interactive prompts
- ❌ Do not pass `default=` as a flat list to `questionary.checkbox` — use `Choice(checked=True)`
- ❌ Do not add prompt skip logic anywhere except `_ask()` in `runner.py`

### Dependency & template generation
- ❌ Do not compute dependency lists inline in template rendering — use the mapping dicts

### Filesystem operations
- ❌ Do not hardcode project paths — always resolve via `Path.cwd()` or `_resolve_target()`
- ❌ Do not create projects inside `_INSTALLER_ROOT` — the guard in `new.py` must stay in place
- ❌ Do not use `os.path` — use `pathlib.Path` throughout

### Session state
- ❌ Do not leave temp JSON files behind — always clean up in `finally`

---

## Testing Rules

- Tests live in `tests/` mirroring the `installer/` package structure
- Use `pytest`; run with `.venv/bin/python -m pytest`
- Mock `questionary` calls — never trigger real interactive prompts in tests
- Mock `_ask` at `installer.prompts.runner._ask` when testing `run_prompts()`
- Use `tmp_path` fixture for all filesystem operations in tests
- Use `typer.testing.CliRunner` for command-level tests
- Test the guard (`_guard_installer_dir`) and path resolution (`_resolve_target`) as pure functions
- Group related tests inside a class named `Test<Subject>`
- `get_prompt()` returns `PromptDef | None`; always assert `is not None` before passing to `_ask()`
- Use the `_answers(**kwargs)` helper pattern to build `Answers` instances with sensible defaults

### Mock targets table

| What to test | What to mock | Mock target |
|---|---|---|
| `run_prompts()` | `_ask()` | `installer.prompts.runner._ask` |
| `new` command (integration) | `run_prompts` + `create_project` | `installer.commands.new.run_prompts`, `installer.commands.new.create_project` |
| `create_project()` (git) | `_git_init` | `installer.generator.scaffold._git_init` |
| Guard / path resolution | nothing — test as pure functions | — |

### When to add tests

Always add tests when:
- Adding a new `PROMPTS` entry in `definitions.py`
- Adding a new skip rule to `_ask()`
- Adding a new stub template in `stubs/`
- Adding a new dependency mapping to `toml_builder.py`
- Changing `_resolve_target()` path-priority logic
