from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from installer.__main__ import app
from installer.commands.new import _resolve_target, _INSTALLER_ROOT
from installer.models.answers import Answers

runner = CliRunner()


def _mock_run_prompts(answers: Answers, skip_name: bool, temp_path: Path) -> Answers:
    if not answers.project_name:
        answers.project_name = "prompted-app"
    answers.version = "0.1.0"
    answers.git = False
    answers.docker = "venv"
    answers.db_driver = "none"
    answers.db_abstraction = "none"
    answers.testing_frameworks = ["pytest"]
    answers.logging = True
    answers.env_parsing = "dotenv"
    answers.cli_support = "none"
    answers.optional_deps = []
    return answers


class TestResolveTarget:
    def test_plain_name_with_explicit_path(self, tmp_path):
        name, target = _resolve_target("my-app", str(tmp_path))
        assert name == "my-app"
        assert target == str(tmp_path / "my-app")

    def test_plain_name_no_path_uses_cwd(self):
        name, target = _resolve_target("my-app", None)
        assert name == "my-app"
        assert target == str(Path.cwd() / "my-app")

    def test_absolute_path_in_name(self, tmp_path):
        abs_name = str(tmp_path / "my-app")
        name, target = _resolve_target(abs_name, None)
        assert name == "my-app"
        assert target == str(tmp_path / "my-app")

    def test_relative_path_in_name(self, tmp_path):
        # e.g. installer new ../my-app
        name, target = _resolve_target("../my-app", None)
        assert name == "my-app"
        expected = str((Path.cwd() / "../my-app").resolve())
        assert target == expected

    def test_absolute_path_in_name_ignores_explicit_path(self, tmp_path):
        abs_name = str(tmp_path / "sub" / "my-app")
        name, target = _resolve_target(abs_name, "/some/other/dir")
        assert name == "my-app"
        assert target == str((tmp_path / "sub" / "my-app").resolve())


class TestGuardInstallerDir:
    def test_aborts_when_target_inside_installer_root(self):
        target_inside = _INSTALLER_ROOT / "test-app"
        with patch("installer.commands.new.run_prompts", side_effect=_mock_run_prompts):
            result = runner.invoke(
                app, ["new", str(target_inside)]
            )
        assert result.exit_code != 0
        assert "python-installer source" in result.output

    def test_aborts_before_prompts_when_cwd_is_installer_root(self):
        """Guard fires immediately — run_prompts must never be called."""
        with (
            patch("installer.commands.new.Path.cwd", return_value=_INSTALLER_ROOT),
            patch("installer.commands.new.run_prompts", side_effect=_mock_run_prompts) as mock_prompts,
        ):
            result = runner.invoke(app, ["new"])
        assert result.exit_code != 0
        assert "python-installer source" in result.output
        mock_prompts.assert_not_called()


class TestNewCommand:
    def test_new_with_name_arg(self, tmp_path):
        with (
            patch("installer.commands.new.run_prompts", side_effect=_mock_run_prompts),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            result = runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_new_without_name_arg(self, tmp_path):
        with (
            patch("installer.commands.new.run_prompts", side_effect=_mock_run_prompts),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "prompted-app"
            result = runner.invoke(app, ["new", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_new_shows_success_output(self, tmp_path):
        with (
            patch("installer.commands.new.run_prompts", side_effect=_mock_run_prompts),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            result = runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])
        assert "my-app" in result.output

    def test_success_output_venv_shows_venv_steps(self, tmp_path):
        def _venv_answers(answers, skip_name, temp_path):
            _mock_run_prompts(answers, skip_name, temp_path)
            answers.docker = "venv"
            return answers

        with (
            patch("installer.commands.new.run_prompts", side_effect=_venv_answers),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            result = runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])
        assert "python -m venv" in result.output
        assert "docker compose" not in result.output

    def test_success_output_docker_shows_compose_steps(self, tmp_path):
        def _docker_answers(answers, skip_name, temp_path):
            _mock_run_prompts(answers, skip_name, temp_path)
            answers.docker = "docker"
            return answers

        with (
            patch("installer.commands.new.run_prompts", side_effect=_docker_answers),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            result = runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])
        assert "docker compose up --build" in result.output
        assert ".env.example" in result.output
        assert "python -m venv" not in result.output

    def test_success_output_none_shows_pip_steps(self, tmp_path):
        def _none_answers(answers, skip_name, temp_path):
            _mock_run_prompts(answers, skip_name, temp_path)
            answers.docker = "none"
            return answers

        with (
            patch("installer.commands.new.run_prompts", side_effect=_none_answers),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            result = runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])
        assert "pip install" in result.output
        assert "docker compose" not in result.output
        assert "python -m venv" not in result.output

    def test_target_uses_explicit_path(self, tmp_path):
        captured = {}

        def _capture(answers, skip_name, temp_path):
            _mock_run_prompts(answers, skip_name, temp_path)
            captured["target"] = answers.target_path
            return answers

        with (
            patch("installer.commands.new.run_prompts", side_effect=_capture),
            patch("installer.commands.new.create_project") as mock_create,
        ):
            mock_create.return_value = tmp_path / "my-app"
            runner.invoke(app, ["new", "my-app", "--path", str(tmp_path)])

        assert captured["target"] == str(tmp_path / "my-app")

    def test_new_exits_with_error_when_no_name(self, tmp_path):
        def _no_name(answers, skip_name, temp_path):
            answers.project_name = ""
            return answers

        with (
            patch("installer.commands.new.run_prompts", side_effect=_no_name),
            patch("installer.commands.new.create_project"),
        ):
            result = runner.invoke(app, ["new", "--path", str(tmp_path)])
        assert result.exit_code != 0
