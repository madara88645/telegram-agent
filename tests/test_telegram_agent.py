"""Unit tests for telegram_agent.py core logic."""
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers to import the module without a live bot token
# ---------------------------------------------------------------------------

def _import_agent():
    """Import telegram_agent with dummy env vars so module-level code runs."""
    import os
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy")
    os.environ.setdefault("TELEGRAM_USER_ID", "12345")
    os.environ.setdefault("TELEGRAM_WORKSPACE", str(Path(__file__).parent))

    # Re-import cleanly if already loaded
    if "telegram_agent" in sys.modules:
        return sys.modules["telegram_agent"]

    # Insert repo root so `import telegram_agent` works
    repo_root = str(Path(__file__).resolve().parent.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    return importlib.import_module("telegram_agent")


agent = _import_agent()


# ---------------------------------------------------------------------------
# format_output
# ---------------------------------------------------------------------------

class TestFormatOutput:
    def test_empty_string_returns_placeholder(self):
        assert agent.format_output("") == "(Cikti yok)"

    def test_whitespace_only_returns_placeholder(self):
        assert agent.format_output("   ") == "(Cikti yok)"

    def test_normal_text_returned_as_is(self):
        assert agent.format_output("hello") == "hello"

    def test_strips_leading_trailing_whitespace(self):
        assert agent.format_output("  hi  ") == "hi"

    def test_long_text_is_truncated(self):
        long_text = "a" * 4000
        result = agent.format_output(long_text)
        assert len(result) <= agent.MAX_OUTPUT_CHARS + len("\n...(kisaltilmis)")
        assert result.endswith("...(kisaltilmis)")

    def test_text_exactly_at_limit_not_truncated(self):
        text = "x" * agent.MAX_OUTPUT_CHARS
        result = agent.format_output(text)
        assert "...(kisaltilmis)" not in result


# ---------------------------------------------------------------------------
# parse_edit_message
# ---------------------------------------------------------------------------

class TestParseEditMessage:
    def test_valid_edit_message(self):
        msg = "edit myfile.txt\n<<<\nnew content\n>>>"
        result = agent.parse_edit_message(msg)
        assert result is not None
        path, content = result
        assert path == "myfile.txt"
        assert content == "new content"

    def test_missing_edit_prefix_returns_none(self):
        assert agent.parse_edit_message("myfile.txt\n<<<\ncontent\n>>>") is None

    def test_missing_open_delimiter_returns_none(self):
        assert agent.parse_edit_message("edit myfile.txt\nnew content\n>>>") is None

    def test_missing_close_delimiter_returns_none(self):
        assert agent.parse_edit_message("edit myfile.txt\n<<<\nnew content") is None

    def test_multiline_content(self):
        msg = "edit src/app.py\n<<<\nline1\nline2\nline3\n>>>"
        result = agent.parse_edit_message(msg)
        assert result is not None
        path, content = result
        assert path == "src/app.py"
        assert content == "line1\nline2\nline3"

    def test_path_with_subdirectory(self):
        msg = "edit subdir/file.json\n<<<\n{}\n>>>"
        result = agent.parse_edit_message(msg)
        assert result is not None
        assert result[0] == "subdir/file.json"


# ---------------------------------------------------------------------------
# safe_path
# ---------------------------------------------------------------------------

class TestSafePath:
    def test_valid_relative_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(agent, "WORKSPACE_DIR", tmp_path)
        result = agent.safe_path("somefile.txt")
        assert result == tmp_path / "somefile.txt"

    def test_path_traversal_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setattr(agent, "WORKSPACE_DIR", tmp_path)
        result = agent.safe_path("../../etc/passwd")
        assert result is None

    def test_nested_valid_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(agent, "WORKSPACE_DIR", tmp_path)
        result = agent.safe_path("subdir/file.txt")
        assert result == tmp_path / "subdir" / "file.txt"

    def test_workspace_root_itself(self, tmp_path, monkeypatch):
        monkeypatch.setattr(agent, "WORKSPACE_DIR", tmp_path)
        result = agent.safe_path(".")
        # Resolves to workspace dir itself – allowed by the guard
        assert result == tmp_path


# ---------------------------------------------------------------------------
# is_allowed
# ---------------------------------------------------------------------------

class TestIsAllowed:
    def _make_update(self, user_id):
        update = MagicMock()
        update.effective_user.id = user_id
        return update

    def test_allowed_user_returns_true(self, monkeypatch):
        monkeypatch.setattr(agent, "ALLOWED_USER_ID", 99)
        assert agent.is_allowed(self._make_update(99)) is True

    def test_wrong_user_returns_false(self, monkeypatch):
        monkeypatch.setattr(agent, "ALLOWED_USER_ID", 99)
        assert agent.is_allowed(self._make_update(42)) is False

    def test_no_effective_user_returns_false(self, monkeypatch):
        monkeypatch.setattr(agent, "ALLOWED_USER_ID", 99)
        update = MagicMock()
        update.effective_user = None
        assert not agent.is_allowed(update)


# ---------------------------------------------------------------------------
# PendingPlan
# ---------------------------------------------------------------------------

class TestPendingPlan:
    def test_command_plan_creation(self):
        plan = agent.PendingPlan(
            kind="command",
            description="Run tests",
            command=["python", "-m", "pytest"],
        )
        assert plan.kind == "command"
        assert plan.description == "Run tests"
        assert plan.command == ["python", "-m", "pytest"]
        assert plan.file_path is None
        assert plan.new_content is None

    def test_file_edit_plan_creation(self, tmp_path):
        fp = tmp_path / "edit_me.txt"
        plan = agent.PendingPlan(
            kind="file_edit",
            description="Update config",
            file_path=fp,
            new_content="new data",
            diff_text="--- old\n+++ new",
        )
        assert plan.kind == "file_edit"
        assert plan.file_path == fp
        assert plan.new_content == "new data"
        assert plan.diff_text == "--- old\n+++ new"
