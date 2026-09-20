import re

import pytest

from installer.models.answers import Answers
from installer.prompts.definitions import (
    PROMPTS,
    _validate_project_name,
    _validate_version,
    get_prompt,
)


class TestAnswersRoundTrip:
    def test_to_dict_and_from_dict_are_inverse(self):
        original = Answers(
            project_name="my-app",
            version="1.2.3",
            git=False,
            ai_setup=False,
            docker="docker",
            db_driver="postgresql",
            db_abstraction="sqlalchemy",
            testing_frameworks=["pytest", "unittest"],
            logging=True,
            env_parsing="dynaconf",
            cli_support="typer",
            optional_deps=["ruff", "mypy"],
        )
        restored = Answers.from_dict(original.to_dict())
        assert restored.project_name == original.project_name
        assert restored.version == original.version
        assert restored.git is original.git
        assert restored.docker == original.docker
        assert restored.db_driver == original.db_driver
        assert restored.db_abstraction == original.db_abstraction
        assert restored.testing_frameworks == original.testing_frameworks
        assert restored.logging is original.logging
        assert restored.env_parsing == original.env_parsing
        assert restored.cli_support == original.cli_support
        assert restored.optional_deps == original.optional_deps

    def test_from_dict_ignores_unknown_keys(self):
        data = {"project_name": "my-app", "unknown_field": "ignored"}
        restored = Answers.from_dict(data)
        assert restored.project_name == "my-app"
        assert not hasattr(restored, "unknown_field")

    def test_to_dict_contains_all_fields(self):
        a = Answers(project_name="x")
        d = a.to_dict()
        for field in ("project_name", "version", "target_path", "git", "ai_setup",
                      "docker", "db_driver", "db_abstraction", "testing_frameworks",
                      "logging", "env_parsing", "cli_support", "optional_deps"):
            assert field in d


class TestValidateProjectName:
    def test_valid_names(self):
        for name in ["my-app", "my_app", "MyApp", "app.v2", "123"]:
            assert _validate_project_name(name) is True

    def test_rejects_spaces(self):
        result = _validate_project_name("my app")
        assert isinstance(result, str)

    def test_rejects_special_chars(self):
        result = _validate_project_name("my@app!")
        assert isinstance(result, str)

    def test_rejects_empty(self):
        result = _validate_project_name("")
        assert isinstance(result, str)

    def test_rejects_whitespace_only(self):
        result = _validate_project_name("   ")
        assert isinstance(result, str)


class TestValidateVersion:
    def test_valid_version(self):
        assert _validate_version("1.2.3") is True

    def test_rejects_empty(self):
        result = _validate_version("")
        assert isinstance(result, str)


class TestPromptRegistry:
    def test_all_prompts_have_required_fields(self):
        for p in PROMPTS:
            assert p.key
            assert p.prompt_type in ("text", "confirm", "select", "checkbox")
            assert p.message

    def test_select_prompts_have_choices(self):
        for p in PROMPTS:
            if p.prompt_type == "select":
                assert len(p.choices) > 0

    def test_checkbox_prompts_have_choices(self):
        for p in PROMPTS:
            if p.prompt_type == "checkbox":
                assert len(p.choices) > 0

    def test_get_prompt_returns_correct(self):
        p = get_prompt("project_name")
        assert p is not None
        assert p.prompt_type == "text"
        assert p.required is True

    def test_get_prompt_returns_none_for_unknown(self):
        assert get_prompt("nonexistent_key") is None

    def test_docker_prompt_is_select_with_venv_default(self):
        p = get_prompt("docker")
        assert p is not None
        assert p.prompt_type == "select"
        assert p.default == "venv"
        assert "docker" in p.choices
        assert "venv" in p.choices
        assert "none" in p.choices

    def test_twelve_prompts_defined(self):
        assert len(PROMPTS) == 12

    def test_optional_deps_choices(self):
        p = get_prompt("optional_deps")
        assert p is not None
        assert p.prompt_type == "checkbox"
        expected = {"black", "ruff", "flake8", "isort", "mypy", "pyupgrade", "bandit", "detect-secrets"}
        assert set(p.choices) == expected
        assert "pre-commit" not in p.choices
