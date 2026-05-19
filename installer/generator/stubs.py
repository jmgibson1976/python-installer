from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from installer.models.answers import Answers

_STUBS_DIR = Path(__file__).parent.parent / "stubs"


def _jinja_env(stubs_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(stubs_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def _render_template(env: Environment, template_path: str, context: dict) -> str:
    return env.get_template(template_path).render(**context)


def _stub_context(answers: Answers) -> dict:
    return {
        "project_name": answers.project_name,
        "pkg_name": re.sub(r"[^a-zA-Z0-9_]", "_", answers.project_name),
        "version": answers.version,
        "git": answers.git,
        "ai_setup": answers.ai_setup,
        "db_driver": answers.db_driver,
        "db_abstraction": answers.db_abstraction,
        "testing_frameworks": answers.testing_frameworks,
        "logging_enabled": answers.logging,
        "env_parsing": answers.env_parsing,
        "cli_support": answers.cli_support,
        "docker": answers.docker,
        "use_mock": "mock" in answers.testing_frameworks,
    }


def render_stubs(answers: Answers, project_root: Path) -> None:
    """
    Render and write all applicable stub files into *project_root*.

    Always rendered:
      - README.md
      - src/<pkg>/__init__.py

    Conditionally rendered:
      - .gitignore                            (when git=True)
      - src/<pkg>/env.py                     (when env_parsing=="dotenv" or logging=True)
      - .env.example                          (when env_parsing != "none")
      - <pkg_name>/config.py                  (when env_parsing != "none")
      - configs/settings.toml                 (when env_parsing != "none")
      - <pkg_name>/logging.py                 (when logging=True)
      - docker/runtimes/3.13/Dockerfile       (when docker="docker")
      - docker-compose.yml                    (when docker="docker")
      - src/<pkg>/__main__.py                 (when cli_support != "none")
      - src/<pkg>/commands/__init__.py        (when cli_support != "none")
      - src/<pkg>/commands/hello.py           (when cli_support != "none")
      - docs/cli.md                           (when cli_support != "none")
      - tests/__init__.py                     (when testing_frameworks non-empty)
      - tests/test_sample.py                  (when "pytest" in testing_frameworks)
      - tests/test_sample_unittest.py         (when "unittest" in testing_frameworks)
      - src/<pkg>/database.py                 (when db_driver != "none")
      - docs/database.md                       (when db_driver != "none")
      - database/README.md                     (when db_driver == "nosql")
      - database/migrations/0001_initial.up.sql   (when db_driver is sql)
      - database/migrations/0001_initial.down.sql (when db_driver is sql)
      - database/seeders/001_seed_users.sql    (when db_driver is sql)
      - scripts/migrate.sh                     (when db_driver is sql)
      - scripts/rollback.sh                    (when db_driver is sql)
      - scripts/refresh.sh                     (when db_driver is sql)
      - scripts/seed.sh                        (when db_driver is sql)
      - .github/copilot-instructions.md        (when ai_setup=True)
      - .github/instructions/python.instructions.md  (when ai_setup=True)
      - .github/instructions/test.instructions.md    (when ai_setup=True and testing_frameworks non-empty)
      - .github/instructions/bash.instructions.md    (when ai_setup=True and db_driver is sql or docker=docker)
      - .github/instructions/sql.instructions.md     (when ai_setup=True and db_driver is sql)
      - .github/instructions/docker.instructions.md  (when ai_setup=True and docker=docker)
      - .github/skills/run-tests/SKILL.md      (when ai_setup=True)
      - .github/agents/feature-planner.agent.md (when ai_setup=True)
      - .github/hooks/pre-commit               (when ai_setup=True and git=True; executable)
      - .github/hooks/hooks.json               (when ai_setup=True)
      - .github/prompts/new-feature.prompt.md  (when ai_setup=True and git=True)
      - .github/prompts/plan-feature.prompt.md (when ai_setup=True and git=True)
      - docs/copilot.md                        (when ai_setup=True)
    """
    env = _jinja_env(_STUBS_DIR)
    context = _stub_context(answers)
    pkg_name = re.sub(r"[^a-zA-Z0-9_]", "_", answers.project_name)

    _write(project_root / "README.md", _render_template(env, "README.md.j2", context))
    if answers.git:
        _write(project_root / ".gitignore", _render_template(env, ".gitignore.j2", context))
    _write(
        project_root / "src" / pkg_name / "__init__.py",
        _render_template(env, "__init__.py.j2", context),
    )

    needs_env_module = answers.logging or answers.env_parsing == "dotenv"
    if needs_env_module:
        _write(
            project_root / "src" / pkg_name / "env.py",
            _render_template(env, "env.py.j2", context),
        )

    if answers.env_parsing != "none":
        _write(project_root / ".env.example", _render_template(env, ".env.example.j2", context))
        _write(
            project_root / "src" / pkg_name / "config.py",
            _render_template(env, "config.py.j2", context),
        )
        _write(
            project_root / "configs" / "settings.toml",
            _render_template(env, "configs/settings.toml.j2", context),
        )

    if answers.logging:
        _write(
            project_root / "src" / pkg_name / "logging.py",
            _render_template(env, "logging.py.j2", context),
        )

    if answers.docker == "docker":
        _write(
            project_root / "docker" / "runtimes" / "3.13" / "Dockerfile",
            _render_template(env, "docker/runtimes/3.13/Dockerfile.j2", context),
        )
        _write(
            project_root / "docker-compose.yml",
            _render_template(env, "docker/docker-compose.yml.j2", context),
        )

    if answers.cli_support != "none":
        _write(
            project_root / "src" / pkg_name / "__main__.py",
            _render_template(env, "cli/__main__.py.j2", context),
        )
        _write(
            project_root / "src" / pkg_name / "commands" / "__init__.py",
            _render_template(env, "cli/commands/__init__.py.j2", context),
        )
        _write(
            project_root / "src" / pkg_name / "commands" / "hello.py",
            _render_template(env, "cli/commands/hello.py.j2", context),
        )
        _write(
            project_root / "docs" / "cli.md",
            _render_template(env, "cli/docs.md.j2", context),
        )

    if answers.testing_frameworks:
        _write(project_root / "tests" / "__init__.py", "")
        if "pytest" in answers.testing_frameworks:
            _write(
                project_root / "tests" / "test_sample.py",
                _render_template(env, "tests/test_sample.py.j2", context),
            )
        if "unittest" in answers.testing_frameworks:
            _write(
                project_root / "tests" / "test_sample_unittest.py",
                _render_template(env, "tests/test_sample_unittest.py.j2", context),
            )

    if answers.db_driver != "none":
        _write(
            project_root / "src" / pkg_name / "database.py",
            _render_template(env, "database.py.j2", context),
        )
        _write(
            project_root / "docs" / "database.md",
            _render_template(env, "database/docs.md.j2", context),
        )

        if answers.db_driver == "nosql":
            _write(
                project_root / "database" / "README.md",
                _render_template(env, "database/README.nosql.md.j2", context),
            )
        else:
            _write(
                project_root / "database" / "migrations" / "0001_initial.up.sql",
                _render_template(env, "database/migrations/0001_initial.up.sql.j2", context),
            )
            _write(
                project_root / "database" / "migrations" / "0001_initial.down.sql",
                _render_template(env, "database/migrations/0001_initial.down.sql.j2", context),
            )
            _write(
                project_root / "database" / "seeders" / "001_seed_users.sql",
                _render_template(env, "database/seeders/001_seed_users.sql.j2", context),
            )
            _write_executable(
                project_root / "scripts" / "migrate.sh",
                _render_template(env, "scripts/migrate.sh.j2", context),
            )
            _write_executable(
                project_root / "scripts" / "rollback.sh",
                _render_template(env, "scripts/rollback.sh.j2", context),
            )
            _write_executable(
                project_root / "scripts" / "refresh.sh",
                _render_template(env, "scripts/refresh.sh.j2", context),
            )
            _write_executable(
                project_root / "scripts" / "seed.sh",
                _render_template(env, "scripts/seed.sh.j2", context),
            )

    if answers.ai_setup:
        is_sql_driver = answers.db_driver not in ("none", "nosql")

        _write(
            project_root / ".github" / "copilot-instructions.md",
            _render_template(env, "github/copilot-instructions.md.j2", context),
        )
        _write(
            project_root / ".github" / "instructions" / "python.instructions.md",
            _render_template(env, "github/instructions/python.instructions.md.j2", context),
        )

        if answers.testing_frameworks:
            _write(
                project_root / ".github" / "instructions" / "test.instructions.md",
                _render_template(env, "github/instructions/test.instructions.md.j2", context),
            )

        if is_sql_driver or answers.docker == "docker":
            _write(
                project_root / ".github" / "instructions" / "bash.instructions.md",
                _render_template(env, "github/instructions/bash.instructions.md.j2", context),
            )

        if is_sql_driver:
            _write(
                project_root / ".github" / "instructions" / "sql.instructions.md",
                _render_template(env, "github/instructions/sql.instructions.md.j2", context),
            )

        if answers.docker == "docker":
            _write(
                project_root / ".github" / "instructions" / "docker.instructions.md",
                _render_template(env, "github/instructions/docker.instructions.md.j2", context),
            )

        _write(
            project_root / ".github" / "skills" / "run-tests" / "SKILL.md",
            _render_template(env, "github/skills/run-tests/SKILL.md.j2", context),
        )
        _write(
            project_root / ".github" / "agents" / "feature-planner.agent.md",
            _render_template(env, "github/agents/feature-planner.agent.md.j2", context),
        )

        if answers.git:
            hook_src = _STUBS_DIR / "github" / "hooks" / "pre-commit"
            _write_executable(
                project_root / ".github" / "hooks" / "pre-commit",
                hook_src.read_text(encoding="utf-8"),
            )
            _write(
                project_root / ".github" / "prompts" / "new-feature.prompt.md",
                _render_template(env, "github/prompts/new-feature.prompt.md.j2", context),
            )
            _write(
                project_root / ".github" / "prompts" / "plan-feature.prompt.md",
                _render_template(env, "github/prompts/plan-feature.prompt.md.j2", context),
            )

        _write(
            project_root / ".github" / "hooks" / "hooks.json",
            _render_template(env, "github/hooks/hooks.json.j2", context),
        )
        _write(
            project_root / "docs" / "copilot.md",
            _render_template(env, "docs/copilot.md.j2", context),
        )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_executable(path: Path, content: str) -> None:
    """Write *content* to *path* and set the executable bit."""
    _write(path, content)
    path.chmod(path.stat().st_mode | 0o755)
