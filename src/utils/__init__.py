"""Utility functions for the swim fantasy optimization program."""

SECONDS_PER_MINUTE = 60

def seconds_to_time_str(seconds: float) -> str:
    """Convert seconds to time string."""
    if seconds >= SECONDS_PER_MINUTE:
        minutes = int(seconds // SECONDS_PER_MINUTE)
        seconds = seconds % SECONDS_PER_MINUTE
        return f"{minutes}:{seconds:05.2f}"

    return f"{seconds:05.2f}"
