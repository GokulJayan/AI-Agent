import json
import threading
import time

from .client import client
from .settings import MODEL
from .timing import format_elapsed
from .tools import TOOL_SCHEMAS, run_tool
from .ui import start_status_animation, stop_status_animation


SYSTEM_PROMPT = (
    "Answer according to the user's request. Keep simple factual answers concise. "
    "For how-to, cooking, tutorial, or procedure requests, give clear numbered steps "
    "and include useful ingredients, requirements, or cautions when relevant. "
    "CRITICAL: For any coding questions, programming logic, or script requests, "
    "you MUST wrap the code in Markdown code blocks with the appropriate language "
    "identifier (e.g., ```python). Always provide complete, runnable code. "
    "Do not show private chain-of-thought or hidden reasoning. "
    "When using a tool, rely only on its returned data. For current events or products, "
    "include the relevant date or source when available, and never invent unsupported details."
)


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


def _stream_completion(messages, on_content):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=2048,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        stream=True,
    )
    content_parts = []
    tool_calls = {}

    for chunk in completion:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None)
        if content:
            content_parts.append(content)
            on_content(content)
        for tool_call in getattr(delta, "tool_calls", None) or []:
            _collect_tool_call(tool_calls, tool_call)

    return content_parts, tool_calls


def _append_tool_results(messages, content_parts, tool_calls):
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

    messages.append(
        {
            "role": "assistant",
            "content": "".join(content_parts) or None,
            "tool_calls": assistant_tool_calls,
        }
    )
    messages.extend(tool_results)


def ask(prompt):
    started_at = time.perf_counter()
    print(f"Prompt: {prompt}\n")
    stop_event = threading.Event()
    status_thread = start_status_animation(stop_event)
    response_started = False
    response_parts = []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    def print_content(content):
        nonlocal response_started
        if not response_started:
            stop_status_animation(stop_event, status_thread)
            print()
            response_started = True
        print(content, end="", flush=True)
        response_parts.append(content)

    try:
        for _ in range(4):
            content_parts, tool_calls = _stream_completion(messages, print_content)
            if not tool_calls:
                break
            _append_tool_results(messages, content_parts, tool_calls)

    except Exception as error:
        stop_status_animation(stop_event, status_thread)
        print(f"\nError: {error}")
        return

    finally:
        if not response_started:
            stop_status_animation(stop_event, status_thread, clear=False)

    elapsed = time.perf_counter() - started_at
    print()

    if response_parts:
        print()
        print(f"Responded in {format_elapsed(elapsed)}.")
    else:
        print(f"No response content received ({format_elapsed(elapsed)}).")
