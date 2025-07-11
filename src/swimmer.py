"""Swimmer class."""

from __future__ import annotations

import json
import math
from pathlib import Path

from entry import Entry
from wr_scraper import get_base_times_from_db

FIVE = 5

class Swimmer:
    """Holds all information for a swimmer entered in the meet."""

    def __init__(self, name: str, country: str | None, birthday: str | None, height: float | None, num_days: int) -> None:
        """Cretes a swimmer with the given name, country, birthday, height, and number of days in the meet."""
        self.name = name
        self.country = country
        self.birthday = birthday
        self.height = height
        self.entries = {}
        self.projected_points = [0] * num_days
        self.excluded = False

        # Just a placeholder for the cost, which will figure out how to scrape later once the website is up
        self.sex = None
        self.cost = 25


    def __repr__(self) -> str:
        """Give string representation of the swimmer."""
        return "Name: " + self.name + "\nCountry: " + self.country + "\nBirthday: " + self.birthday + "\nHeight: " + str(self.height)


    def __eq__(self, other: Swimmer) -> bool:
        """Check equality by name."""
        if not isinstance(other, Swimmer):
            return NotImplemented

        if self.name != other.name:
            return False

        if self.name == other.name and self.entries != other.entries:
            print("WARNING: Swimmers with the same name have different entries.")

        return True


    def __hash__(self) -> int:
        """Hash the swimmer by name."""
        return hash(self.name)


    def add_event(self, entry: str) -> None:
        """
        Create and add an entry to the swimmer's entries.

        Keyword Arguments:
            entry: the string representation of the entry to add

        """
        time_text = entry.split()[-1]
        if time_text[-1] not in [str(x) for x in range(10)]:
            return

        time = int(time_text[-5:-3]) + int(time_text[-2:]) / 100

        # If text is longer than 5 characters, it means there are minutes
        if len(time_text) > FIVE:
            time += 60 * int(time_text[:-6])

        event = " ".join(entry.split()[:-1])
        self.entries[event] = Entry(event, round(time, 2))

        # set sex
        if self.sex:
            return

        if event[0] == "W":
            self.sex = "Female"
        elif event[0] == "M":
            self.sex = "Male"
        else:
            msg = f"Swimmer {self.name} has an event that does not start with 'W' or 'M': {event}"
            raise ValueError(msg)


    def update_seeds(self, swimmers: list[Swimmer]) -> None:
        """
        Get this swimmer's seeds for all events they're entered in.

        Keyword Arguments:
            swimmers: all swimmers to go through

        """
        for event in self.entries:
            seed = 1
            for swimmer in swimmers:
                if event in swimmer.entries and swimmer.entries[event] < self.entries[event]:
                    seed += 1
            self.entries[event].seed = seed

    def update_projected_points(self) -> None:
        """Get the projected points for each day of the meet for this swimmer."""
        with Path("cached_data.json").open("r") as json_file:
            data = json.load(json_file)

        # TODO: Make this not have hard coded year and course, and not have to fetch every time (@lrucache?)
        base_times = get_base_times_from_db(2024, "SCM")
        string_keys_schedule = data.get("schedule_data", {}).get("schedule", {})
        schedule = {int(k): v for k, v in string_keys_schedule.items()}

        # Reset projected points for each day to 0
        self.projected_points = [0] * len(self.projected_points)

        for swimmer_event, entry in self.entries.items():
            entry.projected_points = math.floor((base_times[swimmer_event] / entry.time) ** 3 * 1000)
            if entry.excluded:
                continue
            for day, day_events in schedule.items():
                events = [x[0] for x in day_events]
                if swimmer_event in events:
                    self.projected_points[day - 1] += entry.projected_points
