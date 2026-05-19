import pytest

from installer.generator.toml_builder import build_dependencies, render_toml
from installer.models.answers import Answers


def _answers(**kwargs) -> Answers:
    base = Answers(project_name="my-app", version="0.1.0")
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


class TestBuildDependencies:
    def test_no_selections_returns_empty_runtime(self):
        a = _answers(db_driver="none", db_abstraction="none", env_parsing="none", cli_support="none", logging=False)
        runtime, _ = build_dependencies(a)
        assert runtime == []

    def test_postgresql_adds_psycopg2(self):
        runtime, _ = build_dependencies(_answers(db_driver="postgresql"))
        assert "psycopg2-binary" in runtime

    def test_mysql_adds_pymysql(self):
        runtime, _ = build_dependencies(_answers(db_driver="mysql"))
        assert "pymysql" in runtime

    def test_sqlalchemy_abstraction(self):
        runtime, _ = build_dependencies(_answers(db_abstraction="sqlalchemy"))
        assert "sqlalchemy" in runtime

    def test_dotenv_env_parsing(self):
        a = _answers(env_parsing="dotenv")
        runtime, _ = build_dependencies(a)
        assert "python-dotenv" in runtime

    def test_typer_cli_support(self):
        runtime, _ = build_dependencies(_answers(cli_support="typer"))
        assert "typer" in runtime

    def test_logging_adds_rich_and_dotenv(self):
        runtime, _ = build_dependencies(_answers(logging=True, env_parsing="none"))
        assert "rich" in runtime
        assert "python-dotenv" in runtime

    def test_logging_disabled_no_rich(self):
        runtime, _ = build_dependencies(_answers(logging=False, env_parsing="none"))
        assert "rich" not in runtime

    def test_logging_deduplicates_dotenv_with_env_parsing(self):
        runtime, _ = build_dependencies(_answers(logging=True, env_parsing="dotenv"))
        assert runtime.count("python-dotenv") == 1

    def test_pytest_goes_to_dev(self):
        _, dev = build_dependencies(_answers(testing_frameworks=["pytest"]))
        assert "pytest" in dev

    def test_optional_deps_in_dev(self):
        _, dev = build_dependencies(_answers(optional_deps=["ruff", "black"]))
        assert "ruff" in dev
        assert "black" in dev

    def test_optional_deps_auto_adds_precommit(self):
        _, dev = build_dependencies(_answers(optional_deps=["ruff"]))
        assert "pre-commit" in dev

    def test_no_optional_deps_no_precommit(self):
        _, dev = build_dependencies(_answers(optional_deps=[]))
        assert "pre-commit" not in dev

    def test_pyupgrade_adds_precommit_but_not_pip_package(self):
        _, dev = build_dependencies(_answers(optional_deps=["pyupgrade"]))
        assert "pre-commit" in dev
        assert "pyupgrade" not in dev

    def test_detect_secrets_adds_package(self):
        _, dev = build_dependencies(_answers(optional_deps=["detect-secrets"]))
        assert "detect-secrets" in dev
        assert "pre-commit" in dev

    def test_mypy_adds_package(self):
        _, dev = build_dependencies(_answers(optional_deps=["mypy"]))
        assert "mypy" in dev

    def test_stdlib_drivers_add_no_packages(self):
        runtime, _ = build_dependencies(_answers(db_driver="sqlite"))
        # sqlite3 is stdlib — no extra package
        assert "sqlite3" not in runtime

    def test_no_duplicates(self):
        a = _answers(db_driver="mysql", db_abstraction="sqlalchemy", optional_deps=["ruff"])
        runtime, dev = build_dependencies(a)
        assert len(runtime) == len(set(runtime))
        assert len(dev) == len(set(dev))


class TestRenderToml:
    def test_renders_project_name(self):
        toml = render_toml(_answers())
        assert 'name = "my-app"' in toml

    def test_renders_version(self):
        toml = render_toml(_answers(version="2.0.0"))
        assert 'version = "2.0.0"' in toml

    def test_renders_scripts_entry(self):
        toml = render_toml(_answers())
        assert "my_app.__main__:main" in toml

    def test_renders_dep_in_dependencies(self):
        toml = render_toml(_answers(db_driver="postgresql"))
        assert "psycopg2-binary" in toml

    def test_empty_deps_renders_empty_list(self):
        a = _answers(
            db_driver="none",
            db_abstraction="none",
            env_parsing="none",
            cli_support="none",
            logging=False,
        )
        toml = render_toml(a)
        assert "dependencies = []" in toml

    def test_black_tool_section_when_selected(self):
        toml = render_toml(_answers(optional_deps=["black"]))
        assert "[tool.black]" in toml
        assert "line-length = 88" in toml
        assert 'target-version = ["py313"]' in toml

    def test_black_tool_section_absent_when_not_selected(self):
        toml = render_toml(_answers(optional_deps=[]))
        assert "[tool.black]" not in toml

    def test_isort_tool_section_when_selected(self):
        toml = render_toml(_answers(optional_deps=["isort"]))
        assert "[tool.isort]" in toml
        assert 'profile = "black"' in toml
        assert "line_length = 88" in toml

    def test_isort_tool_section_absent_when_not_selected(self):
        toml = render_toml(_answers(optional_deps=[]))
        assert "[tool.isort]" not in toml

    def test_mypy_tool_section_when_selected(self):
        toml = render_toml(_answers(optional_deps=["mypy"]))
        assert "[tool.mypy]" in toml
        assert "strict = true" in toml
        assert 'python_version = "3.13"' in toml

    def test_mypy_tool_section_absent_when_not_selected(self):
        toml = render_toml(_answers(optional_deps=[]))
        assert "[tool.mypy]" not in toml

    def test_multiple_tool_sections_when_all_selected(self):
        toml = render_toml(_answers(optional_deps=["black", "isort", "mypy"]))
        assert "[tool.black]" in toml
        assert "[tool.isort]" in toml
        assert "[tool.mypy]" in toml

    def test_rendered_toml_is_valid_with_tool_sections(self):
        import tomllib
        toml = render_toml(_answers(optional_deps=["black", "isort", "mypy"]))
        tomllib.loads(toml)  # raises if invalid
