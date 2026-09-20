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
        from installer.prompts.runner import _SKIPPED
        if prompt.key == "project_name" and skip_name:
            return _SKIPPED
        defaults = {
            "project_name": "test-app",
            "version": "0.1.0",
            "git": True,
            "docker": "venv",
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
        assert result.docker == "venv"

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
        assert prompt is not None
        answers = Answers(db_driver="none")
        result = _ask(prompt, answers=answers)
        assert result == "none"

    def test_asks_db_abstraction_when_driver_set(self):
        from installer.prompts.definitions import get_prompt
        from installer.prompts.runner import _ask

        prompt = get_prompt("db_abstraction")
        assert prompt is not None
        answers = Answers(db_driver="postgresql")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "SQLAlchemy (ORM)"
            _ask(prompt, answers=answers)
        mock_q.select.assert_called_once()


class TestMockAutoAddsUnittest:
    """When 'mock' is selected without 'unittest', run_prompts auto-inserts 'unittest'."""

    def _mock_ask_with_mock_only(self, prompt, skip_name=False, answers=None):
        from installer.prompts.runner import _SKIPPED
        if prompt.key == "project_name" and skip_name:
            return _SKIPPED
        defaults = {
            "project_name": "test-app",
            "version": "0.1.0",
            "git": False,
            "ai_setup": False,
            "docker": "none",
            "db_driver": "none",
            "db_abstraction": "none",
            "testing_frameworks": ["mock"],  # mock without unittest
            "logging": False,
            "env_parsing": "none",
            "cli_support": "none",
            "optional_deps": [],
        }
        return defaults.get(prompt.key, prompt.default)

    def test_mock_without_unittest_auto_inserts_unittest(self, tmp_path):
        answers = Answers()
        with patch("installer.prompts.runner._ask", side_effect=self._mock_ask_with_mock_only):
            result = run_prompts(answers, skip_name=False, temp_path=tmp_path / "s.json")
        assert "unittest" in result.testing_frameworks
        assert "mock" in result.testing_frameworks

    def test_unittest_comes_before_mock_when_auto_inserted(self, tmp_path):
        answers = Answers()
        with patch("installer.prompts.runner._ask", side_effect=self._mock_ask_with_mock_only):
            result = run_prompts(answers, skip_name=False, temp_path=tmp_path / "s.json")
        idx_unittest = result.testing_frameworks.index("unittest")
        idx_mock = result.testing_frameworks.index("mock")
        assert idx_unittest < idx_mock

    def test_mock_with_unittest_does_not_duplicate_unittest(self, tmp_path):
        def _ask_with_both(prompt, skip_name=False, answers=None):
            from installer.prompts.runner import _SKIPPED
            if prompt.key == "project_name" and skip_name:
                return _SKIPPED
            defaults = {
                "project_name": "test-app",
                "version": "0.1.0",
                "git": False,
                "ai_setup": False,
                "docker": "none",
                "db_driver": "none",
                "db_abstraction": "none",
                "testing_frameworks": ["unittest", "mock"],
                "logging": False,
                "env_parsing": "none",
                "cli_support": "none",
                "optional_deps": [],
            }
            return defaults.get(prompt.key, prompt.default)

        answers = Answers()
        with patch("installer.prompts.runner._ask", side_effect=_ask_with_both):
            result = run_prompts(answers, skip_name=False, temp_path=tmp_path / "s.json")
        assert result.testing_frameworks.count("unittest") == 1


class TestRunPromptsWithoutTempPath:
    """run_prompts creates its own temp file when temp_path is None."""

    def _minimal_ask(self, prompt, skip_name=False, answers=None):
        from installer.prompts.runner import _SKIPPED
        if prompt.key == "project_name" and skip_name:
            return _SKIPPED
        defaults = {
            "project_name": "test-app",
            "version": "0.1.0",
            "git": False,
            "ai_setup": False,
            "docker": "none",
            "db_driver": "none",
            "db_abstraction": "none",
            "testing_frameworks": ["pytest"],
            "logging": False,
            "env_parsing": "none",
            "cli_support": "none",
            "optional_deps": [],
        }
        return defaults.get(prompt.key, prompt.default)

    def test_run_prompts_with_no_temp_path_returns_answers(self):
        answers = Answers()
        with patch("installer.prompts.runner._ask", side_effect=self._minimal_ask):
            result = run_prompts(answers, skip_name=False, temp_path=None)
        assert result.project_name == "test-app"


class TestWizardAborted:
    """WizardAborted is raised when questionary returns None (Ctrl+C / 'q')."""

    def _get(self, key: str):
        from installer.prompts.definitions import get_prompt
        p = get_prompt(key)
        assert p is not None
        return p

    def test_text_prompt_raises_on_none(self):
        from installer.prompts.runner import WizardAborted, _ask
        prompt = self._get("project_name")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.text.return_value.ask.return_value = None
            with pytest.raises(WizardAborted):
                _ask(prompt)

    def test_confirm_prompt_raises_on_none(self):
        from installer.prompts.runner import WizardAborted, _ask
        prompt = self._get("git")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.confirm.return_value.ask.return_value = None
            with pytest.raises(WizardAborted):
                _ask(prompt)

    def test_select_prompt_raises_on_none(self):
        from installer.prompts.runner import WizardAborted, _ask
        prompt = self._get("db_driver")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = None
            with pytest.raises(WizardAborted):
                _ask(prompt)

    def test_checkbox_prompt_raises_on_none(self):
        from installer.prompts.runner import WizardAborted, _ask
        prompt = self._get("optional_deps")
        with patch("installer.prompts.runner.questionary") as mock_q:
            mock_q.checkbox.return_value.ask.return_value = None
            with pytest.raises(WizardAborted):
                _ask(prompt)

    def test_run_prompts_propagates_wizard_aborted(self, tmp_path):
        from installer.prompts.runner import WizardAborted, run_prompts
        answers = Answers()
        with patch("installer.prompts.runner._ask", side_effect=WizardAborted):
            with pytest.raises(WizardAborted):
                run_prompts(answers, temp_path=tmp_path / "session.json")

    def test_name_skip_returns_skipped_sentinel(self):
        from installer.prompts.runner import _SKIPPED, _ask
        prompt = self._get("project_name")
        result = _ask(prompt, skip_name=True)
        assert result is _SKIPPED
