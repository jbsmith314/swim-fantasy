import sys
import re
import math
import time
from pypdf import PdfReader
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from ortools.linear_solver import pywraplp

class Entry:
    """
    Holds all information for an entry in an event
    """
    def __init__(self, event: str, time: float):
        self.event = event
        self.time = time
        self.seed = None
        self.projected_points = None
    
    def __repr__(self) -> str:
        return "Event: " + self.event + "\nTime: " + self.time + "\nSeed: " + self.seed + "\nProjected points: " + self.projected_points

    def __lt__(self, other):
        return self.time < other.time


class Swimmer:
    """
    Holds all information for a swimmer entered in the meet.
    """
    def __init__(self, name: str, country: str, birthday: str, height: float, num_days: int):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.height = height
        self.entries = {}
        self.projected_points = [0] * num_days
    
    def __repr__(self) -> str:
        return "Name: " + self.name + "\nCountry: " + self.country + "\nBirthday: " + self.birthday + "\nHeight: " + str(self.height)
    
    def add_event(self, entry: str):
        time_text = entry.split()[-1]
        if time_text[-1] not in [str(x) for x in range(10)]:
            return

        time = int(time_text[-5:-3]) + int(time_text[-2:]) / 100
        if len(time_text) > 5:
            time += 60 * int(time_text[:-6])

        event = " ".join(entry.split()[:-1])
        self.entries[event] = Entry(event, round(time, 2))
    
    def update_seeds(self, swimmers):
        for event in self.entries:
            seed = 1
            for swimmer in swimmers:
                if event in swimmer.entries and swimmer.entries[event] < self.entries[event]:
                    seed += 1
            self.entries[event].seed = seed
    
    def update_projected_points(self, base_times: Dict, schedule: Dict):
        for event, entry in self.entries.items():
            entry.projected_points = math.floor((base_times[event] / entry.time) ** 3 * 1000)
            for day in schedule:
                events = [x[0] for x in schedule[day]]
                if event in events:
                    self.projected_points[day - 1] += entry.projected_points

class DataParser:
    def __init__(self):
        self.schedule = None
        self.base_times = None
        self.swimmers = None


    def get_text(self, filename: str) -> str:
        """
        Get all of the text from the pdf.

            Keyword arguments:
            filename: the pdf to extract text from

        Return the full pdf text
        """
        reader = PdfReader(filename)

        text = ""
        for page in reader.pages:
            text += page.extract_text()

        return text


    def is_overhead(self, line: str) -> bool:
        """
        Check if a line of text is overhead from the psych sheet or
        part of an event entry.

            Keyword arguments:
            line: line of text to check

        Return if the line is overhead
        """
        # Check if it's an event entry
        is_event_entry = bool(re.search("en's", line))
        if is_event_entry:
            return False

        # Check if it's a country name
        is_country_name = bool(re.search("[A-Z][A-Z][A-Z] - ", line))
        if is_country_name:
            return False

        return True


    def delete_overhead(self, lines: List[str]) -> List[str]:
        """
        Remove all overhead lines from lines.

            Keyword arguments:
            lines: the list of lines to be filtered

        Return the filtered list of lines
        """
        filtered_lines = list(filter(lambda x: not self.is_overhead(x), lines))
        clean_lines = list(map(lambda x: x.strip(), filtered_lines))

        return clean_lines


    def get_entries(self, filename):
        pdf_text = self.get_text(filename)

        lines = pdf_text.split("\n")
        cutoff = lines.index("Entry List by NAT")
        entry_lines = lines[cutoff:]

        filtered_lines = self.delete_overhead(entry_lines)
        return filtered_lines


    def get_event(self, line: str) -> Tuple[str, str]:
        """
        Get the event entry and return the rest of the line separate from it.
        """
        try:
            cutoff = line.index("  -  ")
            other = line[:cutoff]
            event = line[cutoff + 5:]
        except:
            cutoff = line.index('"')
            other = line[:cutoff + 1]
            event = line[cutoff + 2:]

        return event, other


    def get_height(self, text: str) -> Tuple[float, str]:
        if text[-1] == '"':
            height = float(text.split()[-3])
            rest = " ".join(text.split()[:-3])
            return height, rest
        else:
            return None, text


    def get_birthday(self, text: str) -> Tuple[str, str]:
        birthday = " ".join(text.split()[-3:])
        name = " ".join(text.split()[:-3])
        return birthday, name


    def update_seeds(self, swimmers: List[Swimmer]):
        for swimmer in swimmers:
            swimmer.update_seeds(swimmers)


    def update_projected_points(self, swimmers: List[Swimmer], base_times: Dict, schedule: Dict):
        for swimmer in swimmers:
            swimmer.update_projected_points(base_times, schedule)


    def get_schedule_chunks(self) -> List[str]:
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        url = "https://www.worldaquatics.com/competitions/3433/world-aquatics-swimming-championships-25m-2024/schedule?phase=All"
        driver.get(url)

        # Wait for the page to load fully
        time.sleep(5)  # Adjust this time if the page is taking longer to load

        # Find all elements with the class name "schedule__day"
        lines = driver.find_elements(By.CLASS_NAME, "schedule__day")
        lines_text = [line.text for line in lines]
        driver.quit()

        return lines_text


    def format_event_name(self, event: str) -> str:
        """
        Converts into same event names as on psych sheet.
        """
        partially_corrected = re.sub("m Medley", "m Individual Medley", event)
        corrected_event = re.sub("en ", "en's ", partially_corrected)

        return corrected_event


    def get_base_times(self, base_times_filename: str) -> Dict:
        lines = self.get_text(base_times_filename).split("\n")
        filtered_lines = []
        for line in lines:
            if len(line) < 3:
                continue
            if line.split()[0][-1] == "m" and "Relay" not in line:
                filtered_lines.append(line)
        
        base_times = {}
        for line in filtered_lines:
            event = " ".join(line.split()[:-4])
            women_event_name = self.format_event_name("Women's " + event)
            base_times[women_event_name] = float(line.split()[-1])
            men_event_name = self.format_event_name("Men's " + event)
            base_times[men_event_name] = float(line.split()[-3])
        
        self.base_times = base_times
        return base_times


    def get_schedule(self) -> Dict:
        chunks = self.get_schedule_chunks()
        lines = []
        schedule = {}
        for index, chunk in enumerate(chunks):
            lines = chunk.split("\n")
            day = index + 1
            schedule[day] = []
            for index, line in enumerate(lines):
                if line.split()[0][-2:] == "en" and "Relay" not in line and lines[index + 1] != "Heats":
                    schedule[day].append((self.format_event_name(line), lines[index + 1]))
        
        self.schedule = schedule
        return schedule
    

    def get_swimmers(self, psych_sheet_filename: str) -> List[Swimmer]:
        """
        Get a list of swimmers and their events
        """
        num_days = len(self.schedule)
        lines = self.get_entries(psych_sheet_filename)
        swimmers = []
        country = None
        for line in lines:
            if line[3:6] == " - ":
                country = line[6:]
            elif line[:5] == "Women" or line[:3] == "Men":
                if len(swimmers) == 0:
                    raise Exception("No swimmers to add the event to")
                swimmers[-1].add_event(line)
            else:
                event, rest = self.get_event(line)
                height, rest = self.get_height(rest)
                birthday, name = self.get_birthday(rest)
                new_swimmer = Swimmer(name, country, birthday, height, num_days)
                new_swimmer.add_event(event)
                swimmers.append(new_swimmer)
        
        self.swimmers = swimmers
        return swimmers

class IntegerProgram:
    def __init__(self):
        # Mixed integer program solver
        self.solver = pywraplp.Solver.CreateSolver("SAT")

    def add_constraint(self, constraint: str):
        exec("self.solver.Add(" + constraint + ")")

def check_valid_input() -> bool:
    """
    Checks valid command line input to run the program.

    Returns if the input is valid
    """
    if len(sys.argv) != 3:
        raise Exception("takes two additional arguments")

    psych_sheet = sys.argv[1]
    if psych_sheet[-4:] != ".pdf":
        raise Exception("psych sheet file must be a pdf")
    
    base_times = sys.argv[2]
    if base_times[-4:] != ".pdf":
        raise Exception("base times file must be a pdf")

    return True


def main():
    check_valid_input()

    psych_sheet_filename = sys.argv[1]
    base_times_filename = sys.argv[2]
    parser = DataParser()
    base_times = parser.get_base_times(base_times_filename)
    schedule = parser.get_schedule()
    swimmers = parser.get_swimmers(psych_sheet_filename)

    parser.update_seeds(swimmers)
    parser.update_projected_points(swimmers, base_times, schedule)

    for swimmer in swimmers:
        print(swimmer.name + ": " + str(swimmer.projected_points))


if __name__ == "__main__":
    main()
