import threading
import time

from .client import client
from .settings import MODEL
from .timing import format_elapsed
from .ui import start_status_animation, stop_status_animation


SYSTEM_PROMPT = "Answer in at most two short sentences. Do not show reasoning."


def ask(prompt):
    started_at = time.perf_counter()
    print(f"Prompt: {prompt}\n")
    stop_event = threading.Event()
    status_thread = start_status_animation(stop_event)
    response_started = False
    response_parts = []

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=128,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            stream=True,
        )

        for chunk in completion:
            if not chunk.choices:
                continue

            content = getattr(chunk.choices[0].delta, "content", None)
            if not content:
                continue

            if not response_started:
                stop_status_animation(stop_event, status_thread)
                print()
                response_started = True

            print(content, end="", flush=True)
            response_parts.append(content)

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
