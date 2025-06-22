"""Swimmer class."""

from __future__ import annotations

import math

from entry import Entry

FIVE = 5

class Swimmer:
    """Holds all information for a swimmer entered in the meet."""

    def __init__(self, name: str, country: str, birthday: str, height: float, num_days: int) -> None:
        """Cretes a swimmer with the given name, country, birthday, height, and number of days in the meet."""
        self.name = name
        self.sex = None
        self.country = country
        self.birthday = birthday
        self.height = height
        self.entries = {}
        self.projected_points = [0] * num_days

        self.cost = 25

    def __repr__(self) -> str:
        """Give string representation of the swimmer."""
        return "Name: " + self.name + "\nCountry: " + self.country + "\nBirthday: " + self.birthday + "\nHeight: " + str(self.height)

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

        if self.sex:
            return

        if event[0] == "W":
            self.sex = "Female"
        elif event[0] == "M":
            self.sex = "Male"
        else:
            msg = f"Swimmer {self.name} has an event that does not start with 'W' or 'M': {event}"
            # TODO: Use a logger instead of print
            print(msg)


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

    def update_projected_points(self, base_times: dict, schedule: dict) -> None:
        """
        Get the projected points for each day of the meet for this swimmer.

        Keyword Arguments:
            base_times: the base times to compare to when calculating points
            schedule: the schedule of which events are on which day

        """
        for event, entry in self.entries.items():
            entry.projected_points = math.floor((base_times[event] / entry.time) ** 3 * 1000)
            for day, day_events in schedule.items():
                events = [x[0] for x in day_events]
                if event in events:
                    self.projected_points[day - 1] += entry.projected_points
