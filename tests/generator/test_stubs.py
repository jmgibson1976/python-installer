import pytest

from installer.generator.stubs import render_stubs
from installer.models.answers import Answers


def _answers(**kwargs) -> Answers:
    base = Answers(project_name="my-app", version="0.1.0")
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


class TestRenderStubs:
    def test_readme_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / "README.md").exists()

    def test_gitignore_created_when_git_enabled(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        assert (tmp_path / ".gitignore").exists()

    def test_gitignore_not_created_when_git_disabled(self, tmp_path):
        render_stubs(_answers(git=False), tmp_path)
        assert not (tmp_path / ".gitignore").exists()

    def test_env_example_always_created(self, tmp_path):
        render_stubs(_answers(env_parsing="python-dotenv"), tmp_path)
        assert (tmp_path / ".env.example").exists()

    def test_env_example_contains_app_port(self, tmp_path):
        render_stubs(_answers(env_parsing="python-dotenv"), tmp_path)
        assert "APP_PORT" in (tmp_path / ".env.example").read_text()

    def test_env_example_not_created_when_env_parsing_none(self, tmp_path):
        render_stubs(_answers(env_parsing="none"), tmp_path)
        assert not (tmp_path / ".env.example").exists()

    def test_dockerfile_not_created_when_docker_none(self, tmp_path):
        render_stubs(_answers(docker="none"), tmp_path)
        assert not (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").exists()

    def test_dockerfile_not_created_when_docker_venv(self, tmp_path):
        render_stubs(_answers(docker="venv"), tmp_path)
        assert not (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").exists()

    def test_readme_contains_project_name(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "my-app" in content

    def test_readme_venv_shows_venv_instructions(self, tmp_path):
        render_stubs(_answers(docker="venv"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "python -m venv" in content
        assert "docker compose" not in content

    def test_readme_docker_shows_compose_instructions(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "docker compose up --build" in content
        assert "python -m venv" not in content

    def test_readme_docker_shows_env_copy_step(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert ".env.example" in content

    def test_readme_docker_testing_uses_compose(self, tmp_path):
        render_stubs(_answers(docker="docker", testing_frameworks=["pytest"]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "docker compose run" in content
        assert "pytest" in content


class TestDockerStubs:
    def test_dockerfile_created_at_runtime_path(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        assert (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").exists()

    def test_docker_compose_created_at_project_root(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        assert (tmp_path / "docker-compose.yml").exists()

    def test_old_dockerfile_path_not_used(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        assert not (tmp_path / "Dockerfile").exists()

    def test_dockerfile_contains_pkg_name(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").read_text()
        assert "my_app" in content

    def test_dockerfile_no_extra_apk_for_no_db(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="none"), tmp_path)
        content = (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").read_text()
        assert "apk add" not in content

    def test_dockerfile_adds_postgresql_deps(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="postgresql"), tmp_path)
        content = (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").read_text()
        assert "postgresql-dev" in content

    def test_dockerfile_adds_mysql_deps(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="mysql"), tmp_path)
        content = (tmp_path / "docker" / "runtimes" / "3.13" / "Dockerfile").read_text()
        assert "mariadb-dev" in content

    def test_compose_contains_app_service(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "app:" in content

    def test_compose_no_db_service_when_none(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="none"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "db:" not in content

    def test_compose_includes_postgres_service(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="postgresql"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "postgres:" in content
        assert "5432" in content

    def test_compose_includes_mysql_service(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="mysql"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "mysql:" in content
        assert "3306" in content

    def test_compose_includes_mongo_service(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="nosql"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "mongo:" in content
        assert "27017" in content

    def test_compose_includes_named_volume_when_db(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="postgresql"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "my_app_db_data:" in content

    def test_compose_no_volume_when_no_db(self, tmp_path):
        render_stubs(_answers(docker="docker", db_driver="none"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "db_data" not in content

    def test_compose_build_references_runtime_path(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / "docker-compose.yml").read_text()
        assert "docker/runtimes/3.13/Dockerfile" in content


class TestEnvExampleStub:
    def _env_answers(self, **kwargs) -> Answers:
        return _answers(env_parsing="python-dotenv", **kwargs)

    def test_no_db_vars_when_driver_none(self, tmp_path):
        render_stubs(self._env_answers(db_driver="none"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "DATABASE_URL" not in content
        assert "DB_NAME" not in content

    def test_postgresql_vars_present(self, tmp_path):
        render_stubs(self._env_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "DATABASE_URL=postgresql://" in content
        assert "DB_USER" in content
        assert "DB_PASSWORD" in content

    def test_mysql_vars_present(self, tmp_path):
        render_stubs(self._env_answers(db_driver="mysql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "DATABASE_URL=mysql+pymysql://" in content
        assert "DB_ROOT_PASSWORD" in content

    def test_mssql_vars_present(self, tmp_path):
        render_stubs(self._env_answers(db_driver="mssql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "DATABASE_URL=mssql+pyodbc://" in content

    def test_nosql_vars_present(self, tmp_path):
        render_stubs(self._env_answers(db_driver="nosql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "MONGO_URI" in content
        assert "27017" in content

    def test_forward_db_port_included_when_docker_and_db(self, tmp_path):
        render_stubs(self._env_answers(docker="docker", db_driver="postgresql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "FORWARD_DB_PORT" in content

    def test_forward_db_port_excluded_when_no_docker(self, tmp_path):
        render_stubs(self._env_answers(docker="none", db_driver="postgresql"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "FORWARD_DB_PORT" not in content


class TestConfigStub:
    def _dotenv_answers(self, **kwargs) -> Answers:
        return _answers(env_parsing="dotenv", **kwargs)

    def _dynaconf_answers(self, **kwargs) -> Answers:
        return _answers(env_parsing="dynaconf", **kwargs)

    def test_config_py_created_for_dotenv(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "config.py").exists()

    def test_config_py_created_for_dynaconf(self, tmp_path):
        render_stubs(self._dynaconf_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "config.py").exists()

    def test_config_py_not_created_when_env_parsing_none(self, tmp_path):
        render_stubs(_answers(env_parsing="none"), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "config.py").exists()

    def test_settings_toml_created_for_dotenv(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        assert (tmp_path / "configs" / "settings.toml").exists()

    def test_settings_toml_created_for_dynaconf(self, tmp_path):
        render_stubs(self._dynaconf_answers(), tmp_path)
        assert (tmp_path / "configs" / "settings.toml").exists()

    def test_settings_toml_not_created_when_none(self, tmp_path):
        render_stubs(_answers(env_parsing="none"), tmp_path)
        assert not (tmp_path / "configs" / "settings.toml").exists()

    def test_dotenv_config_uses_settings_class(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "class Settings" in content
        assert "dotenv_values" in content
        assert "tomllib" in content

    def test_dynaconf_config_uses_lazy_settings(self, tmp_path):
        render_stubs(self._dynaconf_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "LazySettings" in content
        assert "merge_enabled=True" in content
        assert "load_dotenv=True" in content

    def test_config_contains_pkg_name_root_var(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "MY_APP_ROOT_DIR" in content

    def test_dotenv_config_does_not_use_os_environ(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "os.environ" not in content
        assert "dotenv_values" in content

    def test_dynaconf_config_does_not_use_os_environ(self, tmp_path):
        render_stubs(self._dynaconf_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "os.environ" not in content

    def test_settings_toml_dotenv_has_hardcoded_defaults(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / "configs" / "settings.toml").read_text()
        assert "[app]" in content
        assert 'name = "my-app"' in content
        assert "debug = false" in content

    def test_settings_toml_dynaconf_uses_env_format(self, tmp_path):
        render_stubs(self._dynaconf_answers(), tmp_path)
        content = (tmp_path / "configs" / "settings.toml").read_text()
        assert "[app]" in content
        assert "@format {env[APP_NAME]}" in content
        assert "@format {env[APP_DEBUG]}" in content

    def test_env_example_has_app_vars(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "APP_NAME" in content
        assert "APP_DEBUG" in content
        assert "APP_VERSION" in content

    def test_env_example_has_root_dir_comment(self, tmp_path):
        render_stubs(self._dotenv_answers(), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "MY_APP_ROOT_DIR" in content


class TestLoggingStub:
    def _logging_answers(self, **kwargs) -> Answers:
        return _answers(logging=True, **kwargs)

    def test_logging_config_created_when_logging_enabled(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "logging.py").exists()

    def test_logging_config_not_created_when_disabled(self, tmp_path):
        render_stubs(_answers(logging=False), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "logging.py").exists()

    def test_logging_config_has_init_function(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "def init(" in content

    def test_logging_config_has_get_logger(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "def get_logger(" in content

    def test_logging_config_has_cleanup(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "def _cleanup(" in content

    def test_logging_config_uses_get_env(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "get_env(" in content
        assert "dotenv_values" not in content

    def test_logging_config_contains_pkg_logs_var(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "MY_APP_LOGS_DIR" in content

    def test_logging_config_supports_rich_handler(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "RichHandler" in content

    def test_logging_config_has_date_postfixed_filename(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "logging.py").read_text()
        assert "strftime" in content
        assert ".log" in content

    def test_gitignore_contains_logs_dir_when_logging(self, tmp_path):
        render_stubs(self._logging_answers(), tmp_path)
        content = (tmp_path / ".gitignore").read_text()
        assert "logs/" in content

    def test_gitignore_no_logs_dir_when_logging_disabled(self, tmp_path):
        render_stubs(_answers(logging=False), tmp_path)
        content = (tmp_path / ".gitignore").read_text()
        assert "logs/" not in content

    def test_env_example_has_log_level_when_logging(self, tmp_path):
        render_stubs(self._logging_answers(env_parsing="dotenv"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "LOG_LEVEL" in content
        assert "LOG_RETENTION_DAYS" in content
        assert "LOG_CONSOLE" in content

    def test_env_example_no_log_vars_when_logging_disabled(self, tmp_path):
        render_stubs(_answers(logging=False, env_parsing="dotenv"), tmp_path)
        content = (tmp_path / ".env.example").read_text()
        assert "LOG_LEVEL" not in content


class TestInitStub:
    def test_init_py_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "__init__.py").exists()

    def test_init_py_has_version(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert '__version__' in content
        assert "importlib.metadata" in content
        assert "PackageNotFoundError" in content

    def test_init_py_has_root_dir(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "ROOT_DIR" in content

    def test_init_py_has_logging_setup_when_enabled(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "from my_app.logging import" in content
        assert "_init_logging" in content
        assert "LOGS_DIR" in content

    def test_init_py_no_logging_when_disabled(self, tmp_path):
        render_stubs(_answers(logging=False), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "from my_app.logging import" not in content

    def test_init_py_has_settings_import_when_env_parsing(self, tmp_path):
        render_stubs(_answers(env_parsing="dotenv"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "from my_app.config import settings" in content

    def test_init_py_no_settings_when_env_parsing_none(self, tmp_path):
        render_stubs(_answers(env_parsing="none"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "from my_app.config import settings" not in content

    def test_init_py_sets_pkg_root_env_var(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "MY_APP_ROOT_DIR" in content

    def test_init_py_sets_start_time_env_var(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "MY_APP_START" in content
        assert "START_TIME" in content

    def test_init_py_has_section_comments(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__init__.py").read_text()
        assert "Path constants" in content or "path constants" in content.lower()


class TestEnvStub:
    def test_env_py_created_when_logging_enabled(self, tmp_path):
        render_stubs(_answers(logging=True, env_parsing="none"), tmp_path)
        assert (tmp_path / "src" / "my_app" / "env.py").exists()

    def test_env_py_created_when_dotenv_parsing(self, tmp_path):
        render_stubs(_answers(logging=False, env_parsing="dotenv"), tmp_path)
        assert (tmp_path / "src" / "my_app" / "env.py").exists()

    def test_env_py_not_created_for_dynaconf_without_logging(self, tmp_path):
        render_stubs(_answers(logging=False, env_parsing="dynaconf"), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "env.py").exists()

    def test_env_py_not_created_when_neither(self, tmp_path):
        render_stubs(_answers(logging=False, env_parsing="none"), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "env.py").exists()

    def test_env_py_has_get_env_function(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "env.py").read_text()
        assert "def get_env(" in content

    def test_env_py_has_reload_env_function(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "env.py").read_text()
        assert "def reload_env(" in content

    def test_env_py_uses_cache(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "env.py").read_text()
        assert "_cache" in content

    def test_env_py_uses_pkg_root_env_var(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "env.py").read_text()
        assert "MY_APP_ROOT_DIR" in content

    def test_env_py_does_not_use_os_environ_get_for_values(self, tmp_path):
        render_stubs(_answers(logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "env.py").read_text()
        assert "dotenv_values" in content

    def test_config_py_dotenv_uses_get_env(self, tmp_path):
        render_stubs(_answers(env_parsing="dotenv"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "config.py").read_text()
        assert "get_env(" in content
        assert "from my_app.env import get_env" in content


class TestCliStubs:
    def _typer_answers(self, **kwargs) -> Answers:
        return _answers(cli_support="typer", **kwargs)

    def _argparse_answers(self, **kwargs) -> Answers:
        return _answers(cli_support="argparse", **kwargs)

    # ── File existence ────────────────────────────────────────────────────────

    def test_cli_files_not_created_when_none(self, tmp_path):
        render_stubs(_answers(cli_support="none"), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "__main__.py").exists()
        assert not (tmp_path / "src" / "my_app" / "commands").exists()
        assert not (tmp_path / "docs" / "cli.md").exists()

    def test_cli_files_created_for_typer(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "__main__.py").exists()
        assert (tmp_path / "src" / "my_app" / "commands" / "__init__.py").exists()
        assert (tmp_path / "src" / "my_app" / "commands" / "hello.py").exists()
        assert (tmp_path / "docs" / "cli.md").exists()

    def test_cli_files_created_for_argparse(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        assert (tmp_path / "src" / "my_app" / "__main__.py").exists()
        assert (tmp_path / "src" / "my_app" / "commands" / "__init__.py").exists()
        assert (tmp_path / "src" / "my_app" / "commands" / "hello.py").exists()
        assert (tmp_path / "docs" / "cli.md").exists()

    # ── Typer __main__.py content ─────────────────────────────────────────────

    def test_typer_main_has_app_definition(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "app = typer.Typer(" in content

    def test_typer_main_has_version_callback(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "_version_callback" in content

    def test_typer_main_has_app_callback(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "@app.callback()" in content

    def test_typer_main_has_debug_flag(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "--debug" in content

    def test_typer_main_has_verbose_flag(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "--verbose" in content

    def test_typer_main_registers_hello_command(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert 'app.command("hello")(hello_command)' in content

    def test_typer_main_has_entrypoint(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "def main()" in content
        assert 'if __name__ == "__main__"' in content
        assert "main()" in content

    def test_typer_main_does_not_contain_argparse(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "class App" not in content
        assert "argparse" not in content

    # ── Argparse __main__.py content ──────────────────────────────────────────

    def test_argparse_main_has_app_class(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "class App:" in content

    def test_argparse_main_has_run_method(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "def run(self)" in content

    def test_argparse_main_has_debug_flag(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "--debug" in content

    def test_argparse_main_has_entrypoint(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "def main()" in content
        assert 'if __name__ == "__main__"' in content
        assert "main()" in content

    def test_argparse_main_does_not_contain_typer(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "typer" not in content

    # ── Typer hello.py content ────────────────────────────────────────────────

    def test_typer_hello_has_command_function(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "def hello_command(" in content

    def test_typer_hello_has_count_option(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "--count" in content

    def test_typer_hello_has_upper_flag(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "--upper" in content

    def test_typer_hello_has_debug_panel(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "Panel(" in content

    def test_typer_hello_reads_debug_from_context(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        # debug/verbose must come from ctx.obj, not a per-command --debug flag
        assert "ctx.obj" in content
        assert "ctx: typer.Context" in content

    def test_typer_hello_has_verbose_output(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "verbose" in content

    def test_typer_main_sets_ctx_obj(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "ctx.ensure_object" in content
        assert 'ctx.obj["debug"]' in content
        assert 'ctx.obj["verbose"]' in content

    def test_typer_verbose_present_regardless_of_logging(self, tmp_path):
        render_stubs(self._typer_answers(logging=False), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "--verbose" in content
        assert 'ctx.obj["verbose"]' in content

    # ── Argparse hello.py content ─────────────────────────────────────────────

    def test_argparse_hello_has_register_function(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "def register(" in content

    def test_argparse_hello_has_command_function(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "def hello_command(" in content

    def test_argparse_hello_has_count_option(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "--count" in content

    def test_argparse_hello_has_upper_flag(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "--upper" in content

    def test_argparse_hello_reads_verbose_from_args(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "commands" / "hello.py").read_text()
        assert "args.verbose" in content

    def test_argparse_main_implements_verbose(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "args.verbose" in content
        assert "logging.getLogger" in content

    def test_argparse_verbose_present_regardless_of_logging(self, tmp_path):
        render_stubs(self._argparse_answers(logging=False), tmp_path)
        content = (tmp_path / "src" / "my_app" / "__main__.py").read_text()
        assert "--verbose" in content
        assert "args.verbose" in content

    # ── docs/cli.md content ───────────────────────────────────────────────────

    def test_typer_docs_mentions_debug(self, tmp_path):
        render_stubs(self._typer_answers(), tmp_path)
        content = (tmp_path / "docs" / "cli.md").read_text()
        assert "--debug" in content
        assert "my-app" in content

    def test_argparse_docs_mentions_app_debug(self, tmp_path):
        render_stubs(self._argparse_answers(), tmp_path)
        content = (tmp_path / "docs" / "cli.md").read_text()
        assert "APP_DEBUG" in content


class TestReadmeTechStack:
    def test_tech_stack_section_present(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "## Tech Stack" in content

    def test_sqlite_shown_as_stdlib(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "sqlite3" in content
        assert "stdlib" in content

    def test_postgresql_shown_as_installable(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "psycopg2" in content
        assert "installable" in content

    def test_argparse_shown_as_stdlib(self, tmp_path):
        render_stubs(_answers(cli_support="argparse"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "argparse" in content
        assert "stdlib" in content

    def test_typer_shown_as_installable(self, tmp_path):
        render_stubs(_answers(cli_support="typer"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "typer" in content
        assert "installable" in content

    def test_unittest_shown_as_stdlib(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "unittest" in content
        assert "stdlib" in content

    def test_mock_shown_as_stdlib(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["mock"]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "unittest.mock" in content
        assert "stdlib" in content

    def test_no_db_shows_none(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "Database driver" in content


class TestTestStubs:
    def test_tests_init_created_when_pytest_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        assert (tmp_path / "tests" / "__init__.py").exists()

    def test_tests_init_created_when_unittest_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        assert (tmp_path / "tests" / "__init__.py").exists()

    def test_tests_init_not_created_when_no_frameworks(self, tmp_path):
        render_stubs(_answers(testing_frameworks=[]), tmp_path)
        assert not (tmp_path / "tests" / "__init__.py").exists()

    def test_pytest_sample_created_when_pytest_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        assert (tmp_path / "tests" / "test_sample.py").exists()

    def test_pytest_sample_not_created_when_no_pytest(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        assert not (tmp_path / "tests" / "test_sample.py").exists()

    def test_pytest_sample_contains_def_test(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        content = (tmp_path / "tests" / "test_sample.py").read_text()
        assert "def test_" in content

    def test_unittest_sample_created_when_unittest_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        assert (tmp_path / "tests" / "test_sample_unittest.py").exists()

    def test_unittest_sample_not_created_when_no_unittest(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        assert not (tmp_path / "tests" / "test_sample_unittest.py").exists()

    def test_unittest_sample_contains_testcase(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        content = (tmp_path / "tests" / "test_sample_unittest.py").read_text()
        assert "unittest.TestCase" in content

    def test_mock_import_present_when_mock_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest", "mock"]), tmp_path)
        content = (tmp_path / "tests" / "test_sample_unittest.py").read_text()
        assert "from unittest.mock import" in content

    def test_mock_import_absent_when_mock_not_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["unittest"]), tmp_path)
        content = (tmp_path / "tests" / "test_sample_unittest.py").read_text()
        assert "from unittest.mock import" not in content

    def test_both_files_created_when_both_frameworks(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest", "unittest"]), tmp_path)
        assert (tmp_path / "tests" / "test_sample.py").exists()
        assert (tmp_path / "tests" / "test_sample_unittest.py").exists()


class TestDatabaseStub:
    def test_database_py_created_when_driver_selected(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        assert (tmp_path / "src" / "my_app" / "database.py").exists()

    def test_database_py_not_created_when_no_driver(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        assert not (tmp_path / "src" / "my_app" / "database.py").exists()

    def test_sqlalchemy_orm_when_abstraction_selected(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "DeclarativeBase" in content
        assert "create_engine" in content
        assert "get_session" in content

    def test_raw_sqlite3_when_no_abstraction(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="none"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "sqlite3" in content
        assert "get_connection" in content
        # No ORM imports
        assert "DeclarativeBase" not in content

    def test_raw_mysql_when_mysql_driver_no_abstraction(self, tmp_path):
        render_stubs(_answers(db_driver="mysql", db_abstraction="none"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "pymysql" in content
        assert "get_connection" in content

    def test_raw_postgresql_when_pg_driver_no_abstraction(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql", db_abstraction="none"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "psycopg2" in content
        assert "get_connection" in content

    def test_sqlalchemy_sqlite_orm_crud_functions_present(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        for fn in ("create_user", "get_user", "list_users", "update_user", "delete_user"):
            assert fn in content

    def test_raw_sqlite_crud_functions_present(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="none"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        for fn in ("create_user", "get_user", "list_users", "update_user", "delete_user"):
            assert fn in content

    def test_database_py_created_for_postgresql_with_abstraction(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql", db_abstraction="sqlalchemy"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "psycopg2" in content
        assert "create_engine" in content

    def test_get_env_used_when_env_module_available(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy", env_parsing="dotenv"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "get_env" in content
        assert "from my_app.env import get_env" in content
        assert "os.environ" not in content

    def test_os_environ_used_when_no_env_module(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy", env_parsing="none", logging=False), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "os.environ" in content
        assert "from my_app.env import get_env" not in content

    def test_get_env_used_for_raw_mysql_when_env_available(self, tmp_path):
        render_stubs(_answers(db_driver="mysql", db_abstraction="none", env_parsing="dotenv"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "get_env" in content
        assert "os.environ" not in content

    def test_get_env_used_for_raw_postgresql_when_env_available(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql", db_abstraction="none", env_parsing="dotenv"), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "get_env" in content
        assert "os.environ" not in content

    def test_get_env_used_when_logging_enabled_no_dotenv(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy", env_parsing="none", logging=True), tmp_path)
        content = (tmp_path / "src" / "my_app" / "database.py").read_text()
        assert "get_env" in content


class TestMigrationStubs:
    _SQL_DRIVERS = ["sqlite", "mysql", "mariadb", "postgresql", "mssql", "oracle"]

    def test_migration_up_created_for_sql_drivers(self, tmp_path):
        for driver in self._SQL_DRIVERS:
            sub = tmp_path / driver
            render_stubs(_answers(db_driver=driver), sub)
            assert (sub / "database" / "migrations" / "0001_initial.up.sql").exists(), driver

    def test_migration_down_created_for_sql_drivers(self, tmp_path):
        for driver in self._SQL_DRIVERS:
            sub = tmp_path / driver
            render_stubs(_answers(db_driver=driver), sub)
            assert (sub / "database" / "migrations" / "0001_initial.down.sql").exists(), driver

    def test_seeder_created_for_sql_drivers(self, tmp_path):
        for driver in self._SQL_DRIVERS:
            sub = tmp_path / driver
            render_stubs(_answers(db_driver=driver), sub)
            assert (sub / "database" / "seeders" / "001_seed_users.sql").exists(), driver

    def test_scripts_created_for_sql_drivers(self, tmp_path):
        scripts = ["migrate.sh", "rollback.sh", "refresh.sh", "seed.sh"]
        for driver in self._SQL_DRIVERS:
            sub = tmp_path / driver
            render_stubs(_answers(db_driver=driver), sub)
            for script in scripts:
                assert (sub / "scripts" / script).exists(), f"{driver}: {script}"

    def test_scripts_are_executable(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        import stat
        for script in ("migrate.sh", "rollback.sh", "refresh.sh", "seed.sh"):
            path = tmp_path / "scripts" / script
            assert path.stat().st_mode & stat.S_IXUSR, f"{script} not executable"

    def test_nosql_gets_readme_not_migrations(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        assert (tmp_path / "database" / "README.md").exists()
        assert not (tmp_path / "database" / "migrations").exists()
        assert not (tmp_path / "scripts" / "migrate.sh").exists()

    def test_no_db_gets_no_database_dir(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        assert not (tmp_path / "database").exists()
        assert not (tmp_path / "scripts").exists()

    def test_sqlite_up_uses_autoincrement(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "database" / "migrations" / "0001_initial.up.sql").read_text()
        assert "AUTOINCREMENT" in content

    def test_postgresql_up_uses_serial(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "database" / "migrations" / "0001_initial.up.sql").read_text()
        assert "SERIAL" in content

    def test_mysql_up_uses_auto_increment(self, tmp_path):
        render_stubs(_answers(db_driver="mysql"), tmp_path)
        content = (tmp_path / "database" / "migrations" / "0001_initial.up.sql").read_text()
        assert "AUTO_INCREMENT" in content

    def test_mssql_up_uses_identity(self, tmp_path):
        render_stubs(_answers(db_driver="mssql"), tmp_path)
        content = (tmp_path / "database" / "migrations" / "0001_initial.up.sql").read_text()
        assert "IDENTITY" in content

    def test_down_drops_users_table(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "database" / "migrations" / "0001_initial.down.sql").read_text()
        assert "users" in content.lower()
        assert "drop" in content.lower()

    def test_seeder_inserts_sample_rows(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "database" / "seeders" / "001_seed_users.sql").read_text()
        assert "INSERT" in content
        assert "alice@example.com" in content

    def test_postgresql_seeder_uses_on_conflict(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "database" / "seeders" / "001_seed_users.sql").read_text()
        assert "ON CONFLICT" in content

    def test_migrate_script_uses_psql_for_postgresql(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "scripts" / "migrate.sh").read_text()
        assert "psql" in content

    def test_migrate_script_uses_mysql_for_mysql(self, tmp_path):
        render_stubs(_answers(db_driver="mysql"), tmp_path)
        content = (tmp_path / "scripts" / "migrate.sh").read_text()
        assert "mysql" in content

    def test_migrate_script_uses_sqlite3_for_sqlite(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "scripts" / "migrate.sh").read_text()
        assert "sqlite3" in content

    def test_seed_script_accepts_name_argument(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "scripts" / "seed.sh").read_text()
        # script should branch on $# or $1
        assert "$#" in content or "$1" in content

    def test_seed_script_normalises_sql_extension(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "scripts" / "seed.sh").read_text()
        assert ".sql" in content

    def test_nosql_readme_mentions_mongodb(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        content = (tmp_path / "database" / "README.md").read_text()
        assert "MongoDB" in content or "pymongo" in content


class TestDatabaseDocs:
    def test_docs_database_md_created_for_sql_driver(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        assert (tmp_path / "docs" / "database.md").exists()

    def test_docs_database_md_created_for_nosql(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        assert (tmp_path / "docs" / "database.md").exists()

    def test_docs_database_md_not_created_when_no_driver(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        assert not (tmp_path / "docs" / "database.md").exists()

    def test_nosql_docs_mentions_mongodb(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "MongoDB" in content
        assert "pymongo" in content

    def test_nosql_docs_has_connection_section(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "MONGO_URI" in content

    def test_sqlite_docs_has_database_url(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "DATABASE_URL" in content

    def test_postgresql_docs_has_psycopg2_dsn(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "psycopg2" in content or "postgresql" in content.lower()

    def test_sqlalchemy_docs_has_session_usage(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "SessionFactory" in content

    def test_sqlalchemy_docs_has_model_example(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="sqlalchemy"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "mapped_column" in content or "Mapped" in content

    def test_raw_driver_docs_has_context_manager_example(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite", db_abstraction="none"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "with Database()" in content

    def test_sql_docs_has_migrations_section(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "## Migrations" in content
        assert "migrate.sh" in content

    def test_sql_docs_has_seeders_section(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "## Seeders" in content
        assert "seed.sh" in content

    def test_sql_docs_warns_about_refresh(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        assert "destructive" in content.lower() or "Warning" in content

    def test_sql_docs_has_scripts_table(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "database.md").read_text()
        for script in ("migrate.sh", "rollback.sh", "refresh.sh", "seed.sh"):
            assert script in content

    def test_readme_has_database_section_for_sql(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "## Database" in content
        assert "docs/database.md" in content

    def test_readme_has_database_section_for_nosql(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "## Database" in content
        assert "docs/database.md" in content

    def test_readme_no_database_section_when_no_driver(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "## Database" not in content

    def test_readme_sql_includes_quick_commands(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "migrate.sh" in content
        assert "seed.sh" in content


class TestGithubStubs:
    def test_copilot_instructions_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".github" / "copilot-instructions.md").exists()

    def test_copilot_instructions_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-cool-app"), tmp_path)
        content = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "my-cool-app" in content

    def test_python_instructions_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "python.instructions.md").exists()

    def test_python_instructions_has_apply_to(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "python.instructions.md").read_text()
        assert "applyTo" in content
        assert "**/*.py" in content

    def test_python_instructions_includes_get_env_rule_when_dotenv(self, tmp_path):
        render_stubs(_answers(env_parsing="dotenv"), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "python.instructions.md").read_text()
        assert "get_env" in content

    def test_python_instructions_no_get_env_rule_when_no_env(self, tmp_path):
        render_stubs(_answers(env_parsing="none", logging=False), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "python.instructions.md").read_text()
        assert "get_env" not in content

    def test_test_instructions_created_when_frameworks_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "test.instructions.md").exists()

    def test_test_instructions_not_created_when_no_frameworks(self, tmp_path):
        render_stubs(_answers(testing_frameworks=[]), tmp_path)
        assert not (tmp_path / ".github" / "instructions" / "test.instructions.md").exists()

    def test_test_instructions_has_apply_to(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "test.instructions.md").read_text()
        assert "applyTo" in content
        assert "tests/**/*.py" in content

    def test_bash_instructions_created_when_sql_driver(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "bash.instructions.md").exists()

    def test_bash_instructions_created_when_docker(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "bash.instructions.md").exists()

    def test_bash_instructions_not_created_when_no_db_no_docker(self, tmp_path):
        render_stubs(_answers(db_driver="none", docker="venv"), tmp_path)
        assert not (tmp_path / ".github" / "instructions" / "bash.instructions.md").exists()

    def test_bash_instructions_has_set_euo_pipefail(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "bash.instructions.md").read_text()
        assert "set -euo pipefail" in content

    def test_sql_instructions_created_when_sql_driver(self, tmp_path):
        render_stubs(_answers(db_driver="postgresql"), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "sql.instructions.md").exists()

    def test_sql_instructions_not_created_when_nosql(self, tmp_path):
        render_stubs(_answers(db_driver="nosql"), tmp_path)
        assert not (tmp_path / ".github" / "instructions" / "sql.instructions.md").exists()

    def test_sql_instructions_not_created_when_no_driver(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        assert not (tmp_path / ".github" / "instructions" / "sql.instructions.md").exists()

    def test_sql_instructions_has_apply_to(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "sql.instructions.md").read_text()
        assert "applyTo" in content
        assert "database/**/*.sql" in content

    def test_sql_instructions_contains_driver_specific_section(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "sql.instructions.md").read_text()
        assert "SQLite" in content

    def test_docker_instructions_created_when_docker(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        assert (tmp_path / ".github" / "instructions" / "docker.instructions.md").exists()

    def test_docker_instructions_not_created_when_venv(self, tmp_path):
        render_stubs(_answers(docker="venv"), tmp_path)
        assert not (tmp_path / ".github" / "instructions" / "docker.instructions.md").exists()

    def test_docker_instructions_has_apply_to(self, tmp_path):
        render_stubs(_answers(docker="docker"), tmp_path)
        content = (tmp_path / ".github" / "instructions" / "docker.instructions.md").read_text()
        assert "applyTo" in content
        assert "Dockerfile" in content

    def test_hook_created_when_git(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        assert (tmp_path / ".github" / "hooks" / "pre-commit").exists()

    def test_hook_not_created_when_no_git(self, tmp_path):
        render_stubs(_answers(git=False), tmp_path)
        assert not (tmp_path / ".github" / "hooks" / "pre-commit").exists()

    def test_hook_is_executable(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        hook = tmp_path / ".github" / "hooks" / "pre-commit"
        assert hook.stat().st_mode & 0o111

    def test_hook_has_shebang(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        content = (tmp_path / ".github" / "hooks" / "pre-commit").read_text()
        assert content.startswith("#!/usr/bin/env bash")

    def test_prompt_created_when_git(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        assert (tmp_path / ".github" / "prompts" / "new-feature.prompt.md").exists()

    def test_prompt_not_created_when_no_git(self, tmp_path):
        render_stubs(_answers(git=False), tmp_path)
        assert not (tmp_path / ".github" / "prompts" / "new-feature.prompt.md").exists()

    def test_prompt_has_agent_frontmatter(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "new-feature.prompt.md").read_text()
        assert "agent: ask" in content
        assert "mode:" not in content

    def test_prompt_has_input_variable(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "new-feature.prompt.md").read_text()
        assert "${input:" in content

    def test_prompt_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-project", git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "new-feature.prompt.md").read_text()
        assert "my-project" in content

    def test_copilot_instructions_shows_cli_section_when_cli_support(self, tmp_path):
        render_stubs(_answers(cli_support="typer"), tmp_path)
        content = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "Typer" in content

    def test_copilot_instructions_shows_db_section_when_db_driver(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "sqlite" in content

    def test_copilot_instructions_no_docker_section_when_venv(self, tmp_path):
        render_stubs(_answers(docker="venv"), tmp_path)
        content = (tmp_path / ".github" / "copilot-instructions.md").read_text()
        assert "Docker" not in content

    def test_hooks_json_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".github" / "hooks" / "hooks.json").exists()

    def test_hooks_json_is_valid_json(self, tmp_path):
        import json
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "hooks" / "hooks.json").read_text()
        parsed = json.loads(content)
        assert "hooks" in parsed

    def test_hooks_json_has_post_tool_use(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        import json
        content = json.loads((tmp_path / ".github" / "hooks" / "hooks.json").read_text())
        assert "PostToolUse" in content["hooks"]

    def test_hooks_json_has_pre_tool_use_when_sql_driver(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        import json
        content = json.loads((tmp_path / ".github" / "hooks" / "hooks.json").read_text())
        assert "PreToolUse" in content["hooks"]

    def test_hooks_json_no_pre_tool_use_when_no_db(self, tmp_path):
        render_stubs(_answers(db_driver="none"), tmp_path)
        import json
        content = json.loads((tmp_path / ".github" / "hooks" / "hooks.json").read_text())
        assert "PreToolUse" not in content["hooks"]

    def test_skill_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").exists()

    def test_skill_has_valid_frontmatter_name(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").read_text()
        assert "name: run-tests" in content

    def test_skill_has_description(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").read_text()
        assert "description:" in content

    def test_skill_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-app"), tmp_path)
        content = (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").read_text()
        assert "my-app" in content

    def test_skill_shows_pytest_command_when_pytest_selected(self, tmp_path):
        render_stubs(_answers(testing_frameworks=["pytest"]), tmp_path)
        content = (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").read_text()
        assert "pytest" in content

    def test_agent_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".github" / "agents" / "feature-planner.agent.md").exists()

    def test_agent_has_name_frontmatter(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "agents" / "feature-planner.agent.md").read_text()
        assert "name: feature-planner" in content

    def test_agent_has_argument_hint(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "agents" / "feature-planner.agent.md").read_text()
        assert "argument-hint:" in content

    def test_agent_has_tools_list(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / ".github" / "agents" / "feature-planner.agent.md").read_text()
        assert "tools:" in content

    def test_agent_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-app"), tmp_path)
        content = (tmp_path / ".github" / "agents" / "feature-planner.agent.md").read_text()
        assert "my-app" in content

    def test_agent_mentions_db_when_db_selected(self, tmp_path):
        render_stubs(_answers(db_driver="sqlite"), tmp_path)
        content = (tmp_path / ".github" / "agents" / "feature-planner.agent.md").read_text()
        assert "database.py" in content

    def test_plan_prompt_created_when_git(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        assert (tmp_path / ".github" / "prompts" / "plan-feature.prompt.md").exists()

    def test_plan_prompt_not_created_when_no_git(self, tmp_path):
        render_stubs(_answers(git=False), tmp_path)
        assert not (tmp_path / ".github" / "prompts" / "plan-feature.prompt.md").exists()

    def test_plan_prompt_targets_feature_planner_agent(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "plan-feature.prompt.md").read_text()
        assert "agent: feature-planner" in content

    def test_plan_prompt_has_input_variable(self, tmp_path):
        render_stubs(_answers(git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "plan-feature.prompt.md").read_text()
        assert "${input:" in content

    def test_plan_prompt_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-app", git=True), tmp_path)
        content = (tmp_path / ".github" / "prompts" / "plan-feature.prompt.md").read_text()
        assert "my-app" in content

    # ai_setup gating tests
    def test_github_dir_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / ".github").exists()

    def test_github_dir_created_when_ai_setup_true(self, tmp_path):
        render_stubs(_answers(ai_setup=True), tmp_path)
        assert (tmp_path / ".github").exists()

    def test_copilot_instructions_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / ".github" / "copilot-instructions.md").exists()

    def test_hooks_json_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / ".github" / "hooks" / "hooks.json").exists()

    def test_skill_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / ".github" / "skills" / "run-tests" / "SKILL.md").exists()

    def test_agent_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / ".github" / "agents" / "feature-planner.agent.md").exists()

    def test_prompts_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False, git=True), tmp_path)
        assert not (tmp_path / ".github" / "prompts").exists()

    # docs/copilot.md tests
    def test_copilot_docs_created_when_ai_setup_true(self, tmp_path):
        render_stubs(_answers(ai_setup=True), tmp_path)
        assert (tmp_path / "docs" / "copilot.md").exists()

    def test_copilot_docs_not_created_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        assert not (tmp_path / "docs" / "copilot.md").exists()

    def test_copilot_docs_contains_project_name(self, tmp_path):
        render_stubs(_answers(project_name="my-app", ai_setup=True), tmp_path)
        content = (tmp_path / "docs" / "copilot.md").read_text()
        assert "my-app" in content

    def test_copilot_docs_mentions_db_section_when_db_selected(self, tmp_path):
        render_stubs(_answers(ai_setup=True, db_driver="sqlite"), tmp_path)
        content = (tmp_path / "docs" / "copilot.md").read_text()
        assert "sql.instructions.md" in content

    def test_copilot_docs_no_db_section_when_no_db(self, tmp_path):
        render_stubs(_answers(ai_setup=True, db_driver="none"), tmp_path)
        content = (tmp_path / "docs" / "copilot.md").read_text()
        assert "sql.instructions.md" not in content

    def test_copilot_docs_mentions_prompts_when_git(self, tmp_path):
        render_stubs(_answers(ai_setup=True, git=True), tmp_path)
        content = (tmp_path / "docs" / "copilot.md").read_text()
        assert "new-feature.prompt.md" in content

    def test_copilot_docs_no_prompts_section_when_no_git(self, tmp_path):
        render_stubs(_answers(ai_setup=True, git=False), tmp_path)
        content = (tmp_path / "docs" / "copilot.md").read_text()
        assert "new-feature.prompt.md" not in content

    # README AI section tests
    def test_readme_has_ai_section_when_ai_setup_true(self, tmp_path):
        render_stubs(_answers(ai_setup=True), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "GitHub Copilot" in content
        assert "docs/copilot.md" in content

    def test_readme_no_ai_section_when_ai_setup_false(self, tmp_path):
        render_stubs(_answers(ai_setup=False), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "docs/copilot.md" not in content


class TestPreCommitStub:
    def test_config_generated_when_tools_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["black", "ruff"]), tmp_path)
        assert (tmp_path / ".pre-commit-config.yaml").exists()

    def test_config_not_generated_when_no_tools(self, tmp_path):
        render_stubs(_answers(optional_deps=[]), tmp_path)
        assert not (tmp_path / ".pre-commit-config.yaml").exists()

    def test_hygiene_hooks_always_present(self, tmp_path):
        render_stubs(_answers(optional_deps=["ruff"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "trailing-whitespace" in content
        assert "end-of-file-fixer" in content
        assert "check-added-large-files" in content
        assert "check-merge-conflict" in content
        assert "mixed-line-ending" in content
        assert "check-ast" in content
        assert "debug-statements" in content
        assert "check-yaml" in content
        assert "check-toml" in content

    def test_black_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["black"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "psf/black" in content
        assert "id: black" in content

    def test_black_section_absent_when_not_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["ruff"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "psf/black" not in content

    def test_ruff_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["ruff"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "ruff-pre-commit" in content
        assert "id: ruff" in content

    def test_flake8_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["flake8"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "PyCQA/flake8" in content
        assert "id: flake8" in content

    def test_isort_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["isort"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "PyCQA/isort" in content
        assert "id: isort" in content

    def test_mypy_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["mypy"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "mirrors-mypy" in content
        assert "id: mypy" in content

    def test_pyupgrade_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["pyupgrade"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "asottile/pyupgrade" in content
        assert "id: pyupgrade" in content

    def test_bandit_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["bandit"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "PyCQA/bandit" in content
        assert "id: bandit" in content

    def test_detect_secrets_section_when_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["detect-secrets"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "Yelp/detect-secrets" in content
        assert "id: detect-secrets" in content

    def test_detect_aws_credentials_added_with_detect_secrets(self, tmp_path):
        render_stubs(_answers(optional_deps=["detect-secrets"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "detect-aws-credentials" in content

    def test_detect_aws_credentials_absent_without_detect_secrets(self, tmp_path):
        render_stubs(_answers(optional_deps=["black"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "detect-aws-credentials" not in content

    def test_multiple_tools_all_included(self, tmp_path):
        render_stubs(_answers(optional_deps=["black", "ruff", "mypy", "bandit"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "psf/black" in content
        assert "ruff-pre-commit" in content
        assert "mirrors-mypy" in content
        assert "PyCQA/bandit" in content

    def test_only_single_tool_no_other_tool_sections(self, tmp_path):
        render_stubs(_answers(optional_deps=["isort"]), tmp_path)
        content = (tmp_path / ".pre-commit-config.yaml").read_text()
        assert "psf/black" not in content
        assert "ruff-pre-commit" not in content
        assert "mirrors-mypy" not in content
        assert "PyCQA/bandit" not in content
        assert "Yelp/detect-secrets" not in content


class TestPreCommitDocs:
    def test_docs_generated_when_tools_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["ruff"]), tmp_path)
        assert (tmp_path / "docs" / "pre-commit.md").exists()

    def test_docs_not_generated_when_no_tools(self, tmp_path):
        render_stubs(_answers(optional_deps=[]), tmp_path)
        assert not (tmp_path / "docs" / "pre-commit.md").exists()

    def test_docs_contain_hygiene_section(self, tmp_path):
        render_stubs(_answers(optional_deps=["black"]), tmp_path)
        content = (tmp_path / "docs" / "pre-commit.md").read_text()
        assert "trailing-whitespace" in content
        assert "end-of-file-fixer" in content
        assert "check-merge-conflict" in content

    def test_docs_contain_selected_tool_section(self, tmp_path):
        render_stubs(_answers(optional_deps=["mypy"]), tmp_path)
        content = (tmp_path / "docs" / "pre-commit.md").read_text()
        assert "mypy" in content
        assert "Static type checker" in content

    def test_docs_omit_unselected_tool_section(self, tmp_path):
        render_stubs(_answers(optional_deps=["ruff"]), tmp_path)
        content = (tmp_path / "docs" / "pre-commit.md").read_text()
        assert "Static type checker" not in content
        assert "bandit" not in content

    def test_detect_secrets_setup_instructions_present(self, tmp_path):
        render_stubs(_answers(optional_deps=["detect-secrets"]), tmp_path)
        content = (tmp_path / "docs" / "pre-commit.md").read_text()
        assert ".secrets.baseline" in content

    def test_readme_has_precommit_section_when_tools_selected(self, tmp_path):
        render_stubs(_answers(optional_deps=["black", "ruff"]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "pre-commit" in content
        assert "docs/pre-commit.md" in content

    def test_readme_no_precommit_section_when_no_tools(self, tmp_path):
        render_stubs(_answers(optional_deps=[]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "docs/pre-commit.md" not in content

    def test_readme_lists_selected_tools(self, tmp_path):
        render_stubs(_answers(optional_deps=["mypy", "bandit"]), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "mypy" in content
        assert "bandit" in content


class TestGithooksStubs:
    def test_githooks_created_when_git_and_tools_selected(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["ruff"]), tmp_path)
        assert (tmp_path / ".githooks" / "pre-commit").exists()
        assert (tmp_path / ".githooks" / "prepare-commit-msg").exists()
        assert (tmp_path / ".githooks" / "post-commit").exists()
        assert (tmp_path / ".githooks" / "pre-push").exists()

    def test_githooks_not_created_when_no_tools(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=[]), tmp_path)
        assert not (tmp_path / ".githooks").exists()

    def test_githooks_not_created_when_no_git(self, tmp_path):
        render_stubs(_answers(git=False, optional_deps=["ruff"]), tmp_path)
        assert not (tmp_path / ".githooks").exists()

    def test_pre_commit_hook_is_executable(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["black"]), tmp_path)
        hook = tmp_path / ".githooks" / "pre-commit"
        assert hook.stat().st_mode & 0o111

    def test_pass_through_hooks_are_executable(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["ruff"]), tmp_path)
        for name in ("prepare-commit-msg", "post-commit", "pre-push"):
            assert (tmp_path / ".githooks" / name).stat().st_mode & 0o111

    def test_pre_commit_hook_calls_pre_commit_run(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["mypy"]), tmp_path)
        content = (tmp_path / ".githooks" / "pre-commit").read_text()
        assert "pre-commit run" in content
        assert "hook-stage pre-commit" in content

    def test_pre_commit_hook_graceful_when_not_installed(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["ruff"]), tmp_path)
        content = (tmp_path / ".githooks" / "pre-commit").read_text()
        assert "not installed" in content
        assert "exit 0" in content

    def test_pass_through_delegates_to_copilot_hook(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["black"]), tmp_path)
        for name in ("prepare-commit-msg", "post-commit", "pre-push"):
            content = (tmp_path / ".githooks" / name).read_text()
            assert f".copilot/hooks/{name}" in content
            assert 'exec "$HOOK"' in content

    def test_pre_commit_hook_lists_selected_tools(self, tmp_path):
        render_stubs(_answers(git=True, optional_deps=["ruff", "mypy"]), tmp_path)
        content = (tmp_path / ".githooks" / "pre-commit").read_text()
        assert "ruff" in content
        assert "mypy" in content
