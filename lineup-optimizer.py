import sys
import re
from typing import Dict, List, Tuple
from pypdf import PdfReader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

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
        return "Event: " + self.event + "Time: " + self.time + "Seed: " + self.seed + "Projected points: " + self.projected_points

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
        self.seeds = {}
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
    
    def update_projected_points(self):
        for entry in self.entries:
            entry.projected_points = entry.time / entry.event


def get_text(filename: str) -> str:
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


def is_overhead(line: str) -> bool:
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


def delete_overhead(lines: List[str]) -> List[str]:
    """
    Remove all overhead lines from lines.

        Keyword arguments:
        lines: the list of lines to be filtered

    Return the filtered list of lines
    """
    filtered_lines = list(filter(lambda x: not is_overhead(x), lines))
    clean_lines = list(map(lambda x: x.strip(), filtered_lines))

    return clean_lines


def get_entries():
    filename = sys.argv[1]
    pdf_text = get_text(filename)

    lines = pdf_text.split("\n")
    cutoff = lines.index("Entry List by NAT")
    entry_lines = lines[cutoff:]

    filtered_lines = delete_overhead(entry_lines)
    return filtered_lines


def get_event(line: str) -> Tuple[str, str]:
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


def get_height(text: str) -> Tuple[float, str]:
    if text[-1] == '"':
        height = float(text.split()[-3])
        rest = " ".join(text.split()[:-3])
        return height, rest
    else:
        return None, text


def get_birthday(text: str) -> Tuple[str, str]:
    birthday = " ".join(text.split()[-3:])
    name = " ".join(text.split()[:-3])
    return birthday, name


def get_swimmers(num_days: int) -> List[Swimmer]:
    """
    Get a list of swimmers and their events
    """
    lines = get_entries()
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
            event, rest = get_event(line)
            height, rest = get_height(rest)
            birthday, name = get_birthday(rest)
            new_swimmer = Swimmer(name, country, birthday, height, num_days)
            new_swimmer.add_event(event)
            swimmers.append(new_swimmer)
    
    return swimmers


def update_seeds(swimmers: List[Swimmer]):
    for swimmer in swimmers:
        swimmer.update_seeds(swimmers)


def update_projected_points(swimmers: List[Swimmer], base_times: Dict):
    for swimmer in swimmers:
        swimmer.update_projected_points(base_times)


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


def get_schedule_chunks():
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


def format_event_name(event: str) -> str:
    """
    Converts into same event names as on psych sheet.
    """
    partially_corrected = re.sub("m Medley", "m Individual Medley", event)
    corrected_event = re.sub("en ", "en's ", partially_corrected)
    return corrected_event


def get_base_times() -> Dict:
    filename = sys.argv[2]
    lines = get_text(filename).split("\n")
    filtered_lines = []
    for line in lines:
        if len(line) < 3:
            continue
        if line.split()[0][-1] == "m" and "Relay" not in line:
            filtered_lines.append(line)
    
    base_times = {}
    for line in filtered_lines:
        event = " ".join(line.split()[:-4])
        women_event_name = format_event_name("Women's " + event)
        base_times[women_event_name] = float(line.split()[-1])
        men_event_name = format_event_name("Men's " + event)
        base_times[men_event_name] = float(line.split()[-3])
    
    return base_times


def get_schedule():
    chunks = get_schedule_chunks()
    lines = []
    schedule = {}
    for index, chunk in enumerate(chunks):
        lines = chunk.split("\n")
        day = index + 1
        schedule[day] = []
        for index, line in enumerate(lines):
            if line.split()[0][-2:] == "en" and "Relay" not in line and lines[index + 1] != "Heats":
                schedule[day].append((format_event_name(line), lines[index + 1]))
    
    return schedule


def main():
    check_valid_input()

    base_times = get_base_times()
    schedule = get_schedule()
    swimmers = get_swimmers(len(schedule))

    update_seeds(swimmers)
    update_projected_points(swimmers, base_times)


if __name__ == "__main__":
    main()
