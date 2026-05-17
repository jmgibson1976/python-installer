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

