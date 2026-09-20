import os

from .settings import MODEL


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def print_help():
    print(
        "Commands:\n"
        "  /exit          Exit the chat\n"
        "  /clear         Clear the terminal\n"
        "  /model         Show the configured model\n"
        "  /file PATH     Send a text file as a prompt\n"
        "  /help          Show this help\n"
    )


def handle_command(command):
    if command == "/exit":
        print("Goodbye.")
        return "exit", None

    if command == "/clear":
        clear_terminal()
        return "handled", None

    if command == "/model":
        print(f"Model: {MODEL}")
        return "handled", None

    if command == "/help":
        print_help()
        return "handled", None

    return None, None
