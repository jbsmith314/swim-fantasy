"""Entry class for holding event information."""

from __future__ import annotations


class Entry:
    """Holds all information for an entry in an event."""

    def __init__(self, event: str, time: float) -> None:
        """Initialize an Entry object with the event name and time."""
        self.event = event
        self.time = time
        self.seed = None
        self.projected_points = None

    def __repr__(self) -> str:
        """Return a string representation of the Entry object."""
        return "Event: " + self.event + "\nTime: " + self.time + "\nSeed: " + self.seed + "\nProjected points: " + self.projected_points

    def __lt__(self, other: Entry) -> bool:
        """
        Compare two Entry objects based on their time.

        Keyword Arguments:
            other: the other Entry object to compare against

        """
        return self.time < other.time
