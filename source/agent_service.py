import json
import time
from collections.abc import Iterator

from .client import client
from .settings import MODEL
from .tools import TOOL_SCHEMAS, run_tool

SYSTEM_PROMPT = (
    "Answer according to the user's request. Keep simple factual answers concise. "
    "For how-to, cooking, tutorial, or procedure requests, give clear numbered steps "
    "and include useful ingredients, requirements, or cautions when relevant. "
    "Do not show private chain-of-thought or hidden reasoning. "
    "When using a tool, rely only on its returned data. For current events or products, "
    "include the relevant date or source when available, and never invent unsupported details."
)
MAX_TOOL_ROUNDS = 4


def _collect_tool_call(tool_calls, tool_call):
    call = tool_calls.setdefault(
        tool_call.index,
        {"id": "", "name": "", "arguments": ""},
    )
    if tool_call.id:
        call["id"] = tool_call.id
    function = getattr(tool_call, "function", None)
    if function:
        if function.name:
            call["name"] = function.name
        if function.arguments:
            call["arguments"] += function.arguments


def _completion(messages):
    return client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=512,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        stream=True,
    )


def _run_tools(messages, content_parts, tool_calls):
    assistant_tool_calls = []
    tool_results = []

    for call in tool_calls.values():
        try:
            arguments = json.loads(call["arguments"])
            result = run_tool(call["name"], arguments)
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            result = f"Tool arguments were invalid: {error}"
        except Exception as error:
            result = str(error)

        assistant_tool_calls.append(
            {
                "id": call["id"],
                "type": "function",
                "function": {
                    "name": call["name"],
                    "arguments": call["arguments"],
                },
            }
        )
        tool_results.append(
            {
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            }
        )
        yield {"type": "tool_result", "name": call["name"], "content": result}

    messages.append(
        {
            "role": "assistant",
            "content": "".join(content_parts) or None,
            "tool_calls": assistant_tool_calls,
        }
    )
    messages.extend(tool_results)


def stream_events(prompt: str) -> Iterator[dict]:
    """Yield structured agent events without writing to stdout."""
    started_at = time.perf_counter()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    yield {"type": "prompt", "content": prompt}

    try:
        for round_number in range(MAX_TOOL_ROUNDS):
            content_parts = []
            tool_calls = {}
            yield {"type": "round_start", "round": round_number + 1}

            for chunk in _completion(messages):
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    content_parts.append(content)
                    yield {"type": "content", "content": content}

                for tool_call in getattr(delta, "tool_calls", None) or []:
                    _collect_tool_call(tool_calls, tool_call)

            if not tool_calls:
                break

            for event in _run_tools(messages, content_parts, tool_calls):
                yield event
        else:
            yield {"type": "warning", "content": "Maximum tool rounds reached."}

        yield {
            "type": "done",
            "elapsed": time.perf_counter() - started_at,
        }
    except Exception as error:
        yield {
            "type": "error",
            "content": str(error),
            "elapsed": time.perf_counter() - started_at,
        }
