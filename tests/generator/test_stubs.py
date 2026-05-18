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
