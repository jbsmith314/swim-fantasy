import math
from entry import Entry
from typing import Dict

class Swimmer:
    """
    Holds all information for a swimmer entered in the meet.
    """
    def __init__(self, name: str, country: str, birthday: str, height: float, num_days: int):
        self.name = name
        self.sex = None
        self.country = country
        self.birthday = birthday
        self.height = height
        self.entries = {}
        self.projected_points = [0] * num_days
    
    def __repr__(self) -> str:
        return "Name: " + self.name + "\nCountry: " + self.country + "\nBirthday: " + self.birthday + "\nHeight: " + str(self.height)
    
    def add_event(self, entry: str):
        """
        Create and add an entry to the swimmer's entries.

            Keyword arguments:
            entry: the string representation of the entry to add
        """
        time_text = entry.split()[-1]
        if time_text[-1] not in [str(x) for x in range(10)]:
            return

        time = int(time_text[-5:-3]) + int(time_text[-2:]) / 100
        if len(time_text) > 5:
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
            raise Exception("Unable to identify sex")

    
    def update_seeds(self, swimmers):
        """
        Get this swimmer's seeds for all events they're entered in.

            Keyword arguments:
            swimmers: all swimmers to go through
        """
        for event in self.entries:
            seed = 1
            for swimmer in swimmers:
                if event in swimmer.entries and swimmer.entries[event] < self.entries[event]:
                    seed += 1
            self.entries[event].seed = seed
    
    def update_projected_points(self, base_times: Dict, schedule: Dict):
        """
        Get the projected points for each day of the meet for this swimmer.

            Keyword arguments:
            base_times: the base times to compare to when calculating points
            schedule: the schedule of which events are on which day
        """
        for event, entry in self.entries.items():
            entry.projected_points = math.floor((base_times[event] / entry.time) ** 3 * 1000)
            for day in schedule:
                events = [x[0] for x in schedule[day]]
                if event in events:
                    self.projected_points[day - 1] += entry.projected_points
