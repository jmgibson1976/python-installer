import re

import pytest

from installer.prompts.definitions import (
    PROMPTS,
    _validate_project_name,
    _validate_version,
    get_prompt,
)


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

    def test_eleven_prompts_defined(self):
        assert len(PROMPTS) == 11
