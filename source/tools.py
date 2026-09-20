import ast
import json
import operator
import shlex
import subprocess
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


class ToolError(Exception):
    pass


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _calculate_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](
            _calculate_node(node.left), _calculate_node(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_calculate_node(node.operand))
    raise ToolError("Only numeric arithmetic is supported")


def calculate(expression):
    try:
        tree = ast.parse(expression, mode="eval")
        result = _calculate_node(tree.body)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, ToolError) as error:
        raise ToolError(f"Invalid calculation: {error}") from error
    return str(result)


def web_search(query):
    if DDGS is None:
        raise ToolError("Install ddgs to use web search")

    results = list(DDGS().text(query, max_results=5))
    if not results:
        return "No search results found."
    return json.dumps(results, ensure_ascii=False)


def wikipedia_search(topic):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic.replace(' ', '_'))}"
    request = Request(url, headers={"User-Agent": "AIAgent/1.0"})
    try:
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
    except Exception as error:
        raise ToolError(f"Wikipedia request failed: {error}") from error

    if data.get("type") == "https://mediawiki.org/wiki/HyperSwitch/errors/not_found":
        return f"No Wikipedia page found for {topic}."
    return json.dumps(
        {
            "title": data.get("title"),
            "summary": data.get("extract"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        },
        ensure_ascii=False,
    )


def read_file(path):
    requested = (WORKSPACE_ROOT / path).resolve()
    if requested != WORKSPACE_ROOT and WORKSPACE_ROOT not in requested.parents:
        raise ToolError("File access is limited to the project workspace")
    if not requested.is_file():
        raise ToolError(f"File not found: {path}")
    try:
        return requested.read_text(encoding="utf-8")[:12000]
    except OSError as error:
        raise ToolError(f"Could not read file: {error}") from error


_ALLOWED_COMMANDS = {"pwd", "ls", "find", "git"}
_ALLOWED_GIT_SUBCOMMANDS = {"diff", "log", "status"}


def safe_shell(command):
    arguments = shlex.split(command)
    if not arguments or arguments[0] not in _ALLOWED_COMMANDS:
        raise ToolError(f"Allowed commands: {', '.join(sorted(_ALLOWED_COMMANDS))}")
    if any(token in command for token in ("|", ">", "<", "&&", ";", "`", "$")):
        raise ToolError("Pipes, redirects, chaining, and shell expansion are disabled")
    if arguments[0] == "git" and (
        len(arguments) < 2 or arguments[1] not in _ALLOWED_GIT_SUBCOMMANDS
    ):
        raise ToolError("Allowed git commands: diff, log, status")
    if arguments[0] == "find" and any(
        token in {"-exec", "-execdir", "-delete"} for token in arguments
    ):
        raise ToolError("find execution and deletion flags are disabled")

    try:
        result = subprocess.run(
            arguments,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ToolError(f"Command failed: {error}") from error

    output = (result.stdout + result.stderr).strip()
    return output[:12000] or f"Command exited with code {result.returncode}"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a numeric arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. Prefer recent authoritative "
                "sources, and include dates or source URLs when relevant."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Look up a topic on Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file inside the project workspace.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "safe_shell",
            "description": "Run a read-only allowlisted shell command in the project workspace.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculate": calculate,
    "web_search": web_search,
    "wikipedia_search": wikipedia_search,
    "read_file": read_file,
    "safe_shell": safe_shell,
}


def run_tool(name, arguments):
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        raise ToolError(f"Unknown tool: {name}")
    return function(**arguments)
