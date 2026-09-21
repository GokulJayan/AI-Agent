import json
from types import SimpleNamespace

import pytest

import source.tools as tools
from source.tools import ToolError, calculate, read_file, safe_shell


def test_calculate_expression():
    assert calculate("12 * (3 + 4)") == "84"
    assert calculate("-2 ** 3") == "-8"
    assert calculate("7 / 2") == "3.5"


def test_calculate_rejects_code():
    for expression in ("__import__('os').getcwd()", "True", "", "1 / 0"):
        with pytest.raises(ToolError):
            calculate(expression)


def test_read_file_stays_inside_workspace():
    with pytest.raises(ToolError):
        read_file("../../.env")


def test_read_file_rejects_missing_file():
    with pytest.raises(ToolError, match="File not found"):
        read_file("does-not-exist.txt")


def test_safe_shell_allows_read_only_git():
    assert isinstance(safe_shell("git status --short"), str)


def test_safe_shell_rejects_chaining():
    commands = ("pwd && whoami", "pwd | cat", "pwd > output.txt", "git reset --hard")
    for command in commands:
        with pytest.raises(ToolError):
            safe_shell(command)


def test_safe_shell_rejects_malformed_command():
    with pytest.raises(ToolError):
        safe_shell("'")


def test_safe_shell_rejects_find_execution():
    with pytest.raises(ToolError):
        safe_shell("find . -exec echo unsafe {} \\;")


def test_run_tool_rejects_unknown_name():
    with pytest.raises(ToolError, match="Unknown tool"):
        tools.run_tool("unknown", {})


def test_web_search_serializes_results(monkeypatch):
    class FakeDDGS:
        def text(self, query, max_results):
            assert query == "python"
            assert max_results == 5
            return [{"title": "Python", "href": "https://python.org"}]

    monkeypatch.setattr(tools, "DDGS", FakeDDGS)

    assert json.loads(tools.web_search("python"))[0]["title"] == "Python"


def test_web_search_returns_empty_message(monkeypatch):
    class FakeDDGS:
        def text(self, query, max_results):
            return []

    monkeypatch.setattr(tools, "DDGS", FakeDDGS)
    assert tools.web_search("no results") == "No search results found."


def test_web_search_requires_dependency(monkeypatch):
    monkeypatch.setattr(tools, "DDGS", None)
    with pytest.raises(ToolError, match="Install ddgs"):
        tools.web_search("python")


def test_wikipedia_search_returns_summary(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"{}"

    monkeypatch.setattr(
        tools,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )
    monkeypatch.setattr(
        tools,
        "json",
        SimpleNamespace(
            load=lambda response: {
                "title": "Python",
                "extract": "A programming language.",
                "content_urls": {"desktop": {"page": "https://wikipedia.org"}},
            },
            dumps=json.dumps,
        ),
    )

    result = json.loads(tools.wikipedia_search("Python"))
    assert result["title"] == "Python"
    assert result["summary"] == "A programming language."


def test_wikipedia_search_wraps_network_errors(monkeypatch):
    def fail(request, timeout):
        raise OSError("offline")

    monkeypatch.setattr(tools, "urlopen", fail)
    with pytest.raises(ToolError, match="Wikipedia request failed"):
        tools.wikipedia_search("Python")


def test_safe_shell_wraps_subprocess_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(tools.subprocess, "run", fail)
    with pytest.raises(ToolError, match="Command failed"):
        safe_shell("pwd")
