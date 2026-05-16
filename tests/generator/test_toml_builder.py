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
        a = _answers(db_driver="none", db_abstraction="none", env_parsing="none", cli_support="none")
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

    def test_pytest_goes_to_dev(self):
        _, dev = build_dependencies(_answers(testing_frameworks=["pytest"]))
        assert "pytest" in dev

    def test_optional_deps_in_dev(self):
        _, dev = build_dependencies(_answers(optional_deps=["ruff", "black"]))
        assert "ruff" in dev
        assert "black" in dev

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
        )
        toml = render_toml(a)
        assert "dependencies = []" in toml
