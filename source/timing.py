def format_elapsed(seconds):
    if seconds < 60:
        return f"{seconds:.1f} seconds"

    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{int(minutes)} minutes {remaining_seconds:.1f} seconds"
