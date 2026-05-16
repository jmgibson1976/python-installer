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

    def test_dockerfile_created_when_docker_true(self, tmp_path):
        render_stubs(_answers(docker=True), tmp_path)
        assert (tmp_path / "Dockerfile").exists()

    def test_docker_compose_created_when_docker_true(self, tmp_path):
        render_stubs(_answers(docker=True), tmp_path)
        assert (tmp_path / "docker-compose.yml").exists()

    def test_dockerfile_not_created_when_docker_false(self, tmp_path):
        render_stubs(_answers(docker=False), tmp_path)
        assert not (tmp_path / "Dockerfile").exists()

    def test_readme_contains_project_name(self, tmp_path):
        render_stubs(_answers(), tmp_path)
        content = (tmp_path / "README.md").read_text()
        assert "my-app" in content

    def test_dockerfile_contains_pkg_name(self, tmp_path):
        render_stubs(_answers(docker=True), tmp_path)
        content = (tmp_path / "Dockerfile").read_text()
        assert "my_app" in content
