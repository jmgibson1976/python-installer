---
applyTo: '**/*.py'
---

# Python Instructions (python-installer project)

> Project-specific rules that supplement the global Python conventions at
> `~/.copilot/instructions/python.instructions.md`. Only add new rules or make existing rules
> stricter — never conflict with the global conventions.

## Code Style & Module Conventions

- Begin every module with `from __future__ import annotations`.
- Use `pathlib.Path` for all filesystem paths — never `os.path`.
- Use `rich` console for all user-facing CLI output — never raw `print()`.
- Use `logging` (not `print`) for internal diagnostics.
- Use `field(default_factory=...)` for mutable dataclass field defaults — never a bare literal (e.g. `default=[]`).

## CLI & Prompt Rules

- Apply `@app.callback()` in `__main__.py` to keep Typer in multi-command mode; register commands with `app.command("name")(fn)` there — never apply `@app.command()` inside `commands/*.py`.
- For `questionary.checkbox`, express pre-checked items as `questionary.Choice(title=..., value=..., checked=True/False)` — passing `default=` as a flat list raises `ValueError` at runtime.
- All prompt skip rules belong exclusively in `_ask()` in `runner.py` — nowhere else.

## Dependency Mapping

- When adding a prompt choice that carries pip dependencies, add an entry to the relevant mapping dict in `toml_builder.py` (e.g. `_DB_DRIVER_PACKAGES`). Never compute dependency lists inline inside `render_toml()`.
- If a required mapping key is absent at render time, raise a `KeyError` with a descriptive message rather than silently returning an empty list.

## Error Handling

- Catch specific exceptions — never bare `except:` or silent `except ...: pass` without a comment explaining why.
- Use `typer.echo` + `raise typer.Exit(code=1)` for user-facing fatal errors in command modules; use `logging.exception` for unexpected runtime failures.
- Always clean up temp files in a `finally` block — do not rely on GC or process exit.

## Testing

- Mock `installer.prompts.runner._ask` (not `questionary`) when testing `run_prompts()`.
- Use `typer.testing.CliRunner` for command-level tests.
- Always use `tmp_path` for filesystem operations — never `tempfile` directly.
- `get_prompt()` returns `PromptDef | None`; always assert `is not None` before passing to `_ask()`.
