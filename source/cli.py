import argparse

from .agent import ask
from .commands import handle_command
from .prompts import read_prompt_file


def parse_args():
    parser = argparse.ArgumentParser(description="Chat with the AI agent.")
    parser.add_argument("prompt", nargs="*", help="One-shot prompt")
    parser.add_argument("--file", type=str, help="Read the prompt from a text file")
    return parser.parse_args()


def interactive_chat():
    print("AI agent ready. Type /help for commands.")

    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if not prompt:
            continue

        action, value = handle_command(prompt)
        if action == "exit":
            return
        if action == "handled":
            continue

        if prompt.startswith("/file"):
            file_path = prompt.removeprefix("/file").strip()
            if not file_path:
                print("Usage: /file PATH")
                continue
            prompt = read_prompt_file(file_path)
            if prompt is None:
                continue

        ask(prompt)


def main():
    args = parse_args()

    if args.file:
        prompt = read_prompt_file(args.file)
        if prompt:
            ask(prompt)
        return

    if args.prompt:
        ask(" ".join(args.prompt))
        return

    interactive_chat()
