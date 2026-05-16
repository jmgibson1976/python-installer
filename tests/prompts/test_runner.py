import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from installer.models.answers import Answers
from installer.prompts.runner import run_prompts, _persist


class TestPersist:
    def test_writes_json(self, tmp_path):
        path = tmp_path / "state.json"
        answers = Answers(project_name="my-app", version="1.0.0")
        _persist(answers, path)
        data = json.loads(path.read_text())
        assert data["project_name"] == "my-app"
        assert data["version"] == "1.0.0"

    def test_overwrites_existing(self, tmp_path):
        path = tmp_path / "state.json"
        a = Answers(project_name="first")
        _persist(a, path)
        a.project_name = "second"
        _persist(a, path)
        assert json.loads(path.read_text())["project_name"] == "second"


class TestRunPrompts:
    """run_prompts integration — questionary is mocked out."""

    def _mock_ask(self, prompt, skip_name=False, answers=None):
        """Return sensible defaults for every prompt type."""
        if prompt.key == "project_name" and skip_name:
            return None
        defaults = {
            "project_name": "test-app",
            "version": "0.1.0",
            "git": True,
            "docker": False,
            "db_driver": "none",
            "db_abstraction": "none",
            "testing_frameworks": ["pytest"],
            "logging": True,
            "env_parsing": "dotenv",
            "cli_support": "none",
            "optional_deps": [],
        }
        return defaults.get(prompt.key, prompt.default)

    def test_run_populates_answers(self, tmp_path):
        path = tmp_path / "session.json"
        answers = Answers()

        with patch("installer.prompts.runner._ask", side_effect=self._mock_ask):
            result = run_prompts(answers, skip_name=False, temp_path=path)

        assert result.project_name == "test-app"
        assert result.version == "0.1.0"
        assert result.git is True
        assert result.docker is False

    def test_skips_name_prompt_when_already_set(self, tmp_path):
        path = tmp_path / "session.json"
        answers = Answers(project_name="pre-set")

        with patch("installer.prompts.runner._ask", side_effect=self._mock_ask):
            result = run_prompts(answers, skip_name=True, temp_path=path)

        assert result.project_name == "pre-set"

    def test_persists_state_file(self, tmp_path):
        path = tmp_path / "session.json"
        answers = Answers()

        with patch("installer.prompts.runner._ask", side_effect=self._mock_ask):
            run_prompts(answers, skip_name=False, temp_path=path)

        assert path.exists()
        data = json.loads(path.read_text())
        assert data["project_name"] == "test-app"


class TestDbAbstractionSkip:
    def test_skips_db_abstraction_when_driver_is_none(self):
        from installer.prompts.definitions import get_prompt
        from installer.prompts.runner import _ask

        prompt = get_prompt("db_abstraction")
        answers = Answers(db_driver="none")
        result = _ask(prompt, answers=answers)
        assert result == "none"

    def test_asks_db_abstraction_when_driver_set(self):
        from installer.prompts.definitions import get_prompt
        from installer.prompts.runner import _ask

        prompt = get_prompt("db_abstraction")
        answers = Answers(db_driver="postgresql")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "SQLAlchemy (ORM)"
            _ask(prompt, answers=answers)
        mock_q.select.assert_called_once()
