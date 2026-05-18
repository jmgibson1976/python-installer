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

    def test_gitignore_always_created(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        assert (tmp_path / ".gitignore").exists()

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

