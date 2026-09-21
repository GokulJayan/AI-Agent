from types import SimpleNamespace

import source.agent as agent


def make_chunk(content=None, tool_calls=None):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def make_tool_call(index, call_id=None, name=None, arguments=None):
    function = SimpleNamespace(name=name, arguments=arguments)
    return SimpleNamespace(
        index=index,
        id=call_id,
        function=function,
    )


def test_tool_messages_follow_assistant_tool_call():
    messages = [{"role": "user", "content": "calculate 2 + 2"}]
    calls = {
        0: {
            "id": "call-1",
            "name": "calculate",
            "arguments": '{"expression":"2 + 2"}',
        }
    }

    agent._append_tool_results(messages, [], calls)

    assert messages[-2]["role"] == "assistant"
    assert messages[-2]["tool_calls"][0]["id"] == "call-1"
    assert messages[-1] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "4",
    }


def test_stream_completion_collects_content_and_tool_call(monkeypatch):
    chunks = [
        make_chunk(content=None, tool_calls=[make_tool_call(0, "call-1", "calculate", '{"expression":')]),
        make_chunk(content=None, tool_calls=[make_tool_call(0, arguments='"2 + 2"}')]),
    ]

    def fake_create(**kwargs):
        assert kwargs["stream"] is True
        assert kwargs["tools"] == agent.TOOL_SCHEMAS
        return chunks

    monkeypatch.setattr(agent.client.chat.completions, "create", fake_create)
    received = []

    content, tool_calls = agent._stream_completion([], received.append)

    assert content == []
    assert tool_calls[0]["id"] == "call-1"
    assert tool_calls[0]["name"] == "calculate"
    assert tool_calls[0]["arguments"] == '{"expression":"2 + 2"}'
    assert received == []


def test_stream_completion_forwards_content(monkeypatch):
    chunks = [make_chunk("Hello"), make_chunk(" world")]
    monkeypatch.setattr(
        agent.client.chat.completions,
        "create",
        lambda **kwargs: chunks,
    )
    received = []

    content, tool_calls = agent._stream_completion([], received.append)

    assert content == ["Hello", " world"]
    assert received == ["Hello", " world"]
    assert tool_calls == {}


def test_ask_runs_tool_then_prints_follow_up(monkeypatch, capsys):
    tool_calls = {
        0: {
            "id": "call-1",
            "name": "calculate",
            "arguments": '{"expression":"2 + 2"}',
        }
    }
    responses = iter([([], tool_calls), (["The answer is 4."], {})])

    def fake_stream(messages, on_content):
        content, calls = next(responses)
        for part in content:
            on_content(part)
        return content, calls

    monkeypatch.setattr(agent, "start_status_animation", lambda event: None)
    monkeypatch.setattr(agent, "stop_status_animation", lambda *args, **kwargs: None)
    monkeypatch.setattr(agent, "_stream_completion", fake_stream)

    agent.ask("What is 2 + 2?")

    output = capsys.readouterr().out
    assert "The answer is 4." in output
    assert "Responded in" in output


def test_ask_reports_no_content(monkeypatch, capsys):
    monkeypatch.setattr(agent, "start_status_animation", lambda event: None)
    monkeypatch.setattr(agent, "stop_status_animation", lambda *args, **kwargs: None)
    monkeypatch.setattr(agent, "_stream_completion", lambda *args: ([], {}))

    agent.ask("No content")

    assert "No response content received" in capsys.readouterr().out
