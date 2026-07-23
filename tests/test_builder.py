"""
tests/test_builder.py — Unit tests for the project builder utilities.
"""

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from vega.builder import (
    BuildPlan,
    BuildResult,
    ProjectFile,
    ProjectBuilder,
    _strip_fences,
    _file_icon,
)


# ─────────────────────────────────────────────
#  _strip_fences
# ─────────────────────────────────────────────

class TestStripFences:
    def test_strips_python_fence(self):
        text = "```python\nprint('hello')\n```"
        assert _strip_fences(text) == "print('hello')"

    def test_strips_plain_fence(self):
        text = "```\nsome content\n```"
        assert _strip_fences(text) == "some content"

    def test_no_fence_unchanged(self):
        text = "just plain text"
        assert _strip_fences(text) == "just plain text"

    def test_strips_leading_trailing_whitespace(self):
        text = "  \nhello\n  "
        assert _strip_fences(text) == "hello"

    def test_json_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert _strip_fences(text) == '{"key": "value"}'

    def test_fence_with_extra_whitespace(self):
        text = "```\n\ncontent\n\n```"
        result = _strip_fences(text)
        assert "content" in result

    def test_empty_string(self):
        assert _strip_fences("") == ""

    def test_only_fences(self):
        assert _strip_fences("```\n```") == ""


# ─────────────────────────────────────────────
#  _file_icon
# ─────────────────────────────────────────────

class TestFileIcon:
    def test_python_icon(self):
        assert _file_icon(".py") == "🐍"

    def test_js_icon(self):
        assert _file_icon(".js") == "📜"

    def test_html_icon(self):
        assert _file_icon(".html") == "🌐"

    def test_markdown_icon(self):
        assert _file_icon(".md") == "📝"

    def test_unknown_extension_default(self):
        assert _file_icon(".xyz") == "📄"

    def test_case_insensitive(self):
        assert _file_icon(".PY") == "🐍"
        assert _file_icon(".JS") == "📜"

    def test_gitignore(self):
        assert _file_icon(".gitignore") == "🚫"

    def test_env_icon(self):
        assert _file_icon(".env") == "🔑"

    def test_rust_icon(self):
        assert _file_icon(".rs") == "🦀"

    def test_go_icon(self):
        assert _file_icon(".go") == "🐹"


# ─────────────────────────────────────────────
#  ProjectFile dataclass
# ─────────────────────────────────────────────

class TestProjectFile:
    def test_creates_correctly(self):
        f = ProjectFile(path="src/main.py", content="print('hello')")
        assert f.path == "src/main.py"
        assert f.content == "print('hello')"


# ─────────────────────────────────────────────
#  BuildPlan dataclass
# ─────────────────────────────────────────────

class TestBuildPlan:
    def test_creates_correctly(self):
        plan = BuildPlan(
            description="A todo app",
            stack=["Python", "FastAPI"],
            files=["main.py", "requirements.txt"],
            instructions="Simple REST API",
        )
        assert plan.description == "A todo app"
        assert "FastAPI" in plan.stack
        assert len(plan.files) == 2


# ─────────────────────────────────────────────
#  BuildResult
# ─────────────────────────────────────────────

class TestBuildResult:
    def _make_result(self, files=None, errors=None, success=True) -> BuildResult:
        plan = BuildPlan("desc", ["Python"], ["main.py"], "instructions")
        # Use sentinel to distinguish None (not passed) from [] (empty list)
        _files = [ProjectFile("main.py", "content")] if files is None else files
        _errors = [] if errors is None else errors
        return BuildResult(
            goal="build a test app",
            plan=plan,
            files=_files,
            output_dir=Path("./test_out"),
            zip_path=None,
            success=success,
            errors=_errors,
        )

    def test_file_count(self):
        result = self._make_result(files=[
            ProjectFile("a.py", ""),
            ProjectFile("b.py", ""),
        ])
        assert result.file_count == 2

    def test_file_count_zero(self):
        assert self._make_result(files=[]).file_count == 0

    def test_success_flag(self):
        assert self._make_result(success=True).success is True
        assert self._make_result(success=False).success is False

    def test_errors_list(self):
        result = self._make_result(errors=["main.py: timeout"])
        assert "main.py: timeout" in result.errors


# ─────────────────────────────────────────────
#  ProjectBuilder._plan — JSON parsing
# ─────────────────────────────────────────────

class TestProjectBuilderPlan:
    def _make_builder(self, tmp_path) -> ProjectBuilder:
        provider = MagicMock()
        return ProjectBuilder(provider=provider, output_dir=tmp_path, verbose=False)

    def test_parses_valid_json_plan(self, tmp_path):
        builder = self._make_builder(tmp_path)
        raw_response = json.dumps({
            "description": "A todo API",
            "stack": ["Python", "FastAPI"],
            "files": ["main.py", "requirements.txt"],
            "instructions": "Simple REST API with SQLite",
        })
        # Mock the provider stream to return the JSON
        chunk = MagicMock()
        chunk.text = raw_response
        builder.provider.stream_with_retry.return_value = iter([chunk])

        plan = builder._plan("build a todo API")

        assert plan.description == "A todo API"
        assert "FastAPI" in plan.stack
        assert "main.py" in plan.files
        assert "SQLite" in plan.instructions

    def test_parses_json_wrapped_in_fences(self, tmp_path):
        builder = self._make_builder(tmp_path)
        raw_response = '```json\n{"description":"X","stack":["A"],"files":["f.py"],"instructions":"Y"}\n```'
        chunk = MagicMock()
        chunk.text = raw_response
        builder.provider.stream_with_retry.return_value = iter([chunk])

        plan = builder._plan("build X")
        assert plan.description == "X"

    def test_fallback_on_invalid_json(self, tmp_path):
        builder = self._make_builder(tmp_path)
        chunk = MagicMock()
        chunk.text = "this is not json at all"
        builder.provider.stream_with_retry.return_value = iter([chunk])

        plan = builder._plan("some goal")
        # Should fall back gracefully
        assert isinstance(plan.files, list)
        assert len(plan.files) > 0


# ─────────────────────────────────────────────
#  ProjectBuilder._generate_one_file
# ─────────────────────────────────────────────

class TestGenerateOneFile:
    def test_returns_file_content(self, tmp_path):
        provider = MagicMock()
        chunk = MagicMock()
        chunk.text = "print('hello world')"
        provider.stream_with_retry.return_value = iter([chunk])

        builder = ProjectBuilder(provider=provider, output_dir=tmp_path, verbose=False)
        plan = BuildPlan("desc", ["Python"], ["main.py"], "instructions")
        content = builder._generate_one_file(plan, "main.py")

        assert "print" in content

    def test_strips_fences_from_response(self, tmp_path):
        provider = MagicMock()
        chunk = MagicMock()
        chunk.text = "```python\nprint('hello')\n```"
        provider.stream_with_retry.return_value = iter([chunk])

        builder = ProjectBuilder(provider=provider, output_dir=tmp_path, verbose=False)
        plan = BuildPlan("desc", ["Python"], ["main.py"], "instructions")
        content = builder._generate_one_file(plan, "main.py")

        assert "```" not in content
        assert "print('hello')" in content

    def test_error_handling(self, tmp_path):
        provider = MagicMock()
        provider.stream_with_retry.side_effect = Exception("network error")

        builder = ProjectBuilder(provider=provider, output_dir=tmp_path, verbose=False)
        plan = BuildPlan("desc", ["Python"], ["main.py"], "instructions")
        content = builder._generate_one_file(plan, "main.py")

        # Should return a comment explaining the error, not raise
        assert "Error" in content
        assert len(builder._errors) == 1
