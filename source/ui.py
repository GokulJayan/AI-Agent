import random
import sys
import threading


STATUS_WORDS = (
    "Fetching",
    "Brewing",
    "Thinking",
    "Processing",
    "Working",
    "Analyzing",
    "Computing",
    "Preparing",
    "Generating",
    "Connecting",
    "Decoding",
    "Calculating",
    "Searching",
    "Reasoning",
    "Cooking",
)


def show_status(stop_event):
    previous_word = None

    while not stop_event.is_set():
        available_words = [
            word for word in STATUS_WORDS
            if word != previous_word
        ]
        word = random.choice(available_words)
        previous_word = word

        for dots in range(4):
            if stop_event.is_set():
                break

            status = f"{word}{'.' * dots}"
            print(f"\r{status:<30}", end="", flush=True)
            stop_event.wait(0.5)


def clear_status():
    print("\r\033[2K", end="", flush=True)


def start_status_animation(stop_event):
    if not sys.stdout.isatty():
        return None

    status_thread = threading.Thread(
        target=show_status,
        args=(stop_event,),
        daemon=True,
    )
    status_thread.start()
    return status_thread


def stop_status_animation(stop_event, status_thread, clear=True):
    stop_event.set()
    if status_thread:
        status_thread.join()
        if clear:
            clear_status()
