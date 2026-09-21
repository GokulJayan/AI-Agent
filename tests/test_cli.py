from source.commands import handle_command
from source.prompts import read_prompt_file


def test_command_handler_exit():
    action, value = handle_command("/exit")
    assert action == "exit"
    assert value is None


def test_command_handler_unknown():
    action, value = handle_command("not-a-command")
    assert action is None
    assert value is None


def test_read_prompt_file(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("  Explain testing.  ", encoding="utf-8")

    assert read_prompt_file(str(prompt_file)) == "Explain testing."


def test_read_prompt_file_empty(tmp_path):
    prompt_file = tmp_path / "empty.txt"
    prompt_file.write_text("   ", encoding="utf-8")

    assert read_prompt_file(str(prompt_file)) is None


def test_read_prompt_file_missing(tmp_path):
    assert read_prompt_file(str(tmp_path / "missing.txt")) is None
