from pathlib import Path


def read_prompt_file(file_path):
    path = Path(file_path).expanduser()
    try:
        prompt = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        print(f"Could not read file: {error}")
        return None

    if not prompt:
        print("The prompt file is empty.")
        return None

    return prompt
