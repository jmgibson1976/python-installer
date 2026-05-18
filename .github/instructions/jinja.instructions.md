---
applyTo: "installer/stubs/**/*.j2"
---

# Jinja2 Stub Instructions (python-installer project)

## Environment Variables in Stubs

Every configurable value introduced in any stub template (`docker-compose.yml.j2`, `config.py.j2`, `configs/settings.toml.j2`, etc.) **must** have a corresponding entry in `.env.example.j2`. This ensures the generated project's `.env.example` documents every variable a developer needs to set.

Rules:
- If a new env var is referenced in any `.j2` template, add it to `.env.example.j2` in the appropriate section.
- Never read configurable values from `os.environ` — use `dotenv_values()` to read from `.env` directly. `os.environ` is susceptible to stale shell variables.
- For dynaconf templates, reference env vars using `@format {env[VAR_NAME]}` syntax so the TOML file delegates to environment rather than hardcoding values.

## Template Authoring

- All stub templates live under `installer/stubs/` and use the `.j2` extension.
- The Jinja2 environment uses `StrictUndefined` — every variable referenced in a template **must** be present in the context dict passed to `render_stubs()`. Missing variables raise a `jinja2.UndefinedError` immediately; they do not silently render as empty strings.
- Keep templates minimal — only include variables that are explicitly defined in `Answers` or the stub context built by `stubs.py`.

## Dockerfile Templates

- Do not use Jinja2 control blocks (`{% %}`) or expressions (`{{ }}`) for Docker `EXPOSE` port values if those values are not in `Answers`. Use a hardcoded port instead.
- Docker language servers validate `.j2` files as Dockerfiles and flag Jinja2 syntax as errors. This is a known false positive. Do not remove valid Jinja2 syntax to silence it; instead, disable the Docker language server for the file by adding `# docker-language-server: ignore` as the first comment line.

## Answers Validation & Context Dict

Before calling `render_stubs(answers, project_root)`, the `Answers` object must be fully populated. If a required field (e.g. `project_name`) is empty or `None`, raise a `ValueError` with a message that names the missing field — do not pass an incomplete object to the renderer.

When adding a new template variable, follow these steps **in order**:

1. Add the field to `Answers` in `models/answers.py` (or derive it from an existing field).
2. Add the key to the context dict in `stubs.py` inside `render_stubs()`.
3. Reference the key in the `.j2` template.

Skipping any step will cause a `jinja2.UndefinedError` at scaffolding time because `StrictUndefined` is active.

## Testing Stub Templates

- Use `tmp_path` to render stubs into an isolated directory — never render into the source tree.
- Assert existence of output files for all conditional render paths (both `True` and `False` branches).
- For templated content, assert that at least one key substitution is correct (e.g. `project_name` appears in `README.md`).
- A missing template variable that goes untested will only fail at scaffolding time — always test the full context path.
