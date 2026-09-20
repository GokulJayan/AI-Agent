import threading
import time
import json

from .client import client
from .settings import MODEL
from .timing import format_elapsed
from .tools import TOOL_SCHEMAS, run_tool
from .ui import start_status_animation, stop_status_animation


SYSTEM_PROMPT = (
    "Answer in at most two short sentences. Do not show reasoning. "
    "When using a tool, rely only on its returned data. For current events or products, "
    "include the relevant date or source when available, and never invent unsupported details."
)


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

    try:
        for _ in range(4):
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=128,
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
                    if not response_started:
                        stop_status_animation(stop_event, status_thread)
                        print()
                        response_started = True
                    print(content, end="", flush=True)
                    content_parts.append(content)
                    response_parts.append(content)

                for tool_call in getattr(delta, "tool_calls", None) or []:
                    index = tool_call.index
                    call = tool_calls.setdefault(
                        index,
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

            if not tool_calls:
                break

            assistant_tool_calls = []
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
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": result,
                    }
                )

            messages.insert(
                -len(assistant_tool_calls),
                {
                    "role": "assistant",
                    "content": "".join(content_parts) or None,
                    "tool_calls": assistant_tool_calls,
                },
            )

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
