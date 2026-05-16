---
applyTo: "tests/**/*.py"
---

# Test Instructions (python-installer project)

> Project-specific rules for `tests/**/*.py`. Rules in this file supplement the global standards
> at `~/.copilot/instructions/test.instructions.md`. Global standards apply in all cases; rules
> here add project-specific constraints and do not override the global ones.

## Structure & File Conventions

- Tests live in `tests/` mirroring `installer/` (e.g. `installer/prompts/runner.py` → `tests/prompts/test_runner.py`).
- Group related tests inside a class named `Test<Subject>`.
- Each test file imports only from public module APIs — never reach into private helpers unless explicitly testing them.
- If a test file does not follow this structure (wrong location, missing class grouping, or importing private internals without cause), flag it as a structural violation and correct it before adding new tests.

## Fixtures & Helpers

- Always use `tmp_path` for filesystem operations — never hardcode temp paths or use `tempfile` directly.
- Use the `_answers(**kwargs)` helper pattern to build `Answers` instances with sensible defaults:
  ```python
  def _answers(**kwargs) -> Answers:
      base = Answers(project_name="my-app", version="0.1.0")
      for k, v in kwargs.items():
          setattr(base, k, v)
      return base
  ```
- Use `typer.testing.CliRunner` for all end-to-end command tests; never invoke the CLI via subprocess.

## Mocking Rules

Use the mock targets table below — mock only the layer under test, nothing deeper:

| What to test | What to mock | Mock target |
|---|---|---|
| `run_prompts()` | `_ask()` | `installer.prompts.runner._ask` |
| `new` command (integration) | `run_prompts` + `create_project` | `installer.commands.new.run_prompts`, `installer.commands.new.create_project` |
| `create_project()` (git) | `_git_init` | `installer.generator.scaffold._git_init` |
| Guard / path resolution | nothing — test as pure functions | — |

- Never mock `questionary` directly when testing `run_prompts()` — mock `_ask` instead.
- Always pass a complete `side_effect` callable (not a return value) when mocking `run_prompts` so the `Answers` object is populated correctly.

## None-Guard Pattern

`get_prompt(key)` returns `PromptDef | None`. Always assert before passing to `_ask()`:

```python
prompt = get_prompt("db_abstraction")
assert prompt is not None
result = _ask(prompt, answers=answers)
```

## Conditional Skip Logic

When testing prompt skipping (e.g., `db_abstraction` skipped when `db_driver == "none"`):
- Set the relevant field on an `Answers` instance and call `_ask()` directly.
- Assert the returned value is the expected default, not that the prompt was shown.

## When to Add Tests

Always add tests when:
- Adding a new `PROMPTS` entry in `definitions.py`.
- Adding a new skip rule to `_ask()`.
- Adding a new stub template in `stubs/`.
- Adding a new dependency mapping to `toml_builder.py`.
- Changing `_resolve_target()` path-priority logic.

## Removed or Deprecated Functionality

This project has no deprecated legacy code at this time. If functionality is removed or deprecated in the future:
- Delete the corresponding tests rather than leaving them to fail silently.
- If a prompt, command, or generator feature is intentionally removed, open a search for `test_<feature>` across `tests/` and remove or update every affected test before merging.
