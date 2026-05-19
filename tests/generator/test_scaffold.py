from unittest.mock import patch

import pytest

from installer.generator.scaffold import create_project, _write_secrets_baseline
from installer.models.answers import Answers


def _answers(**kwargs) -> Answers:
    base = Answers(project_name="test-proj", version="0.1.0")
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


class TestCreateProject:
    def test_creates_project_root(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        root = create_project(a)
        assert root.is_dir()

    def test_creates_src_package(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        root = create_project(a)
        assert (root / "src" / "test_proj" / "__init__.py").exists()

    def test_creates_main_module(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        root = create_project(a)
        assert (root / "src" / "test_proj" / "__main__.py").exists()

    def test_creates_tests_dir(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        root = create_project(a)
        assert (root / "tests").is_dir()

    def test_creates_pyproject_toml(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        root = create_project(a)
        assert (root / "pyproject.toml").exists()

    def test_creates_env_files_when_env_parsing_set(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, env_parsing="dotenv")
        root = create_project(a)
        assert (root / ".env.example").exists()

    def test_creates_configs_dir_when_env_parsing_set(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, env_parsing="dotenv")
        root = create_project(a)
        assert (root / "configs").is_dir()

    def test_no_configs_dir_when_env_parsing_none(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, env_parsing="none")
        root = create_project(a)
        assert not (root / "configs").exists()

    def test_no_env_files_when_none(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, env_parsing="none")
        root = create_project(a)
        assert not (root / ".env.example").exists()

    def test_creates_dockerfile_when_docker(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, docker="docker")
        root = create_project(a)
        assert (root / "docker" / "runtimes" / "3.13" / "Dockerfile").exists()

    def test_git_init_called_when_enabled(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=True)
        with patch("installer.generator.scaffold._git_init") as mock_git:
            create_project(a)
            mock_git.assert_called_once()

    def test_git_init_not_called_when_disabled(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False)
        with patch("installer.generator.scaffold._git_init") as mock_git:
            create_project(a)
            mock_git.assert_not_called()

    def test_creates_logs_dir_when_logging_enabled(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, logging=True)
        root = create_project(a)
        assert (root / "logs").is_dir()

    def test_no_logs_dir_when_logging_disabled(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, logging=False)
        root = create_project(a)
        assert not (root / "logs").exists()

    def test_main_stub_uses_get_logger_when_logging(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, logging=True)
        root = create_project(a)
        content = (root / "src" / "test_proj" / "__main__.py").read_text()
        assert "get_logger" in content
        assert "logging.basicConfig" not in content

    def test_main_stub_uses_print_when_no_logging(self, tmp_path):
        a = _answers(target_path=str(tmp_path / "test-proj"), git=False, logging=False)
        root = create_project(a)
        content = (root / "src" / "test_proj" / "__main__.py").read_text()
        assert "print(" in content
        assert "get_logger" not in content


class TestInitSecretsBaseline:
    def test_baseline_written_with_correct_structure(self, tmp_path):
        _write_secrets_baseline(tmp_path)
        baseline = tmp_path / ".secrets.baseline"
        assert baseline.exists()
        import json
        data = json.loads(baseline.read_text())
        assert "version" in data
        assert "results" in data
        assert data["results"] == {}

    def test_baseline_contains_no_plugins(self, tmp_path):
        _write_secrets_baseline(tmp_path)
        import json
        data = json.loads((tmp_path / ".secrets.baseline").read_text())
        assert data["plugins_used"] == []

    def test_baseline_written_when_detect_secrets_in_optional_deps(self, tmp_path):
        a = _answers(
            target_path=str(tmp_path / "test-proj"),
            git=False,
            optional_deps=["detect-secrets"],
        )
        with patch("installer.generator.scaffold._write_secrets_baseline") as mock_baseline:
            create_project(a)
            mock_baseline.assert_called_once()

    def test_baseline_not_written_without_detect_secrets(self, tmp_path):
        a = _answers(
            target_path=str(tmp_path / "test-proj"),
            git=False,
            optional_deps=["black"],
        )
        with patch("installer.generator.scaffold._write_secrets_baseline") as mock_baseline:
            create_project(a)
            mock_baseline.assert_not_called()
