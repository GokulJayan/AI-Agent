import pytest

from source.tools import ToolError, calculate, read_file, safe_shell


def test_calculate_expression():
    assert calculate("12 * (3 + 4)") == "84"


def test_calculate_rejects_code():
    with pytest.raises(ToolError):
        calculate("__import__('os').getcwd()")


def test_read_file_stays_inside_workspace():
    with pytest.raises(ToolError):
        read_file("../../.env")


def test_safe_shell_allows_read_only_git():
    assert isinstance(safe_shell("git status --short"), str)


def test_safe_shell_rejects_chaining():
    with pytest.raises(ToolError):
        safe_shell("pwd && whoami")
