"""DataParser class for parsing psych sheets and schedules from PDF files and web pages."""

import json
import re
import sys
import time
from pathlib import Path

from pypdf import PdfReader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from swimmer import Swimmer
from utils.constants import SCHEDULE_URLS

CACHE_FILE_PATH = Path(__file__).parent.parent.resolve() / "cached_data.json"

class DataParser:
    """DataParser class for parsing psych sheets and schedules from PDF files and web pages."""

    def __init__(self) -> None:
        """Initialize the DataParser with no schedule, base times, or swimmers."""
        self.schedule = None
        self.base_times = None
        self.swimmers = None


    def get_all_data(self) -> None:
        """Get all data needed for the lineup optimizer."""
        try:
            with CACHE_FILE_PATH.open("r") as file:
                data = json.load(file)
        except FileNotFoundError:
            print("Cache file not found. Creating a new cache file.")
            data = {}

        # ------------------------- Get schedule -------------------------
        # If the schedule URL matches the cached one, use the cached schedule, otherwise, fetch a new schedule
        if data.get("schedule_data", {}).get("schedule_url", "") == SCHEDULE_URLS[sys.argv[1]]:
            print("Using cached schedule.")
            # Get cached schedule
            string_keys_schedule = data.get("schedule_data", {}).get("schedule", {})
            # Convert string keys to integers for the schedule
            self.schedule = {int(k): v for k, v in string_keys_schedule.items()}
        else:
            if data.get("schedule_data", {}).get("schedule_url", ""):
                print("Schedule URL has changed. Fetching new schedule.")
            else:
                print("No cached schedule found. Fetching new schedule.")

            self.get_schedule(SCHEDULE_URLS[sys.argv[1]])


        # -------------------------------- Update cache file --------------------------------
        with CACHE_FILE_PATH.open("w") as json_file:
            schedule_data = {
                "schedule_data": {
                    "schedule": self.schedule,
                    "schedule_url": SCHEDULE_URLS[sys.argv[1]],
                },
            }
            json.dump(schedule_data, json_file, indent=4)


    def get_schedule(self, schedule_url: str) -> dict:
        """
        Get the schedule from the schedule URL.

        Keyword Arguments:
            schedule_url: the URL of the schedule to get

        """
        chunks = self._get_schedule_chunks(schedule_url)
        lines = []
        schedule = {}
        for chunk_index, chunk in enumerate(chunks):
            lines = chunk.split("\n")
            day = chunk_index + 1
            schedule[day] = []
            for line_index, line in enumerate(lines):
                if line.split()[0][-2:] == "en" and "Relay" not in line and lines[line_index + 1] != "Heats":
                    schedule[day].append((self._format_event_name(line), lines[line_index + 1]))

        self.schedule = schedule
        return schedule


    def create_swimmers(self) -> list[Swimmer]:
        """Get a list of swimmers and their events."""
        psych_sheet_filename = "PsychSheets/" + sys.argv[1].lower().replace(" ", "-") + "-psych-sheet.pdf"

        num_days = len(self.schedule)
        lines = self._get_entries(psych_sheet_filename)
        swimmers = []
        country = None
        for line in lines:
            if line[3:6] == " - ":
                country = line[6:]
            elif line[:5] == "Women" or line[:3] == "Men":
                if len(swimmers) == 0:
                    msg = "No swimmers to add the event to. Exiting program"
                    sys.exit(msg)
                swimmers[-1].add_event(line)
            else:
                event, rest = self._get_event(line)
                height, rest = self._get_height(rest)
                birthday, name = self._get_birthday(rest)
                new_swimmer = Swimmer(name, country, birthday, height, num_days)
                new_swimmer.add_event(event)
                swimmers.append(new_swimmer)

        self.swimmers = swimmers
        return swimmers


    def update_seeds(self) -> None:
        """Update the seeds for all swimmers."""
        for swimmer in self.swimmers:
            swimmer.update_seeds(self.swimmers)


    def update_projected_points(self) -> None:
        """Update the projected points for all swimmers."""
        for swimmer in self.swimmers:
            swimmer.update_projected_points()


    def _get_text(self, filename: str) -> str:
        """
        Get all of the text from the pdf.

        Keyword Arguments:
            filename: the pdf to extract text from

        """
        try:
            reader = PdfReader(filename)
        except FileNotFoundError:
            msg = f"Psych sheet file '{filename}' not found. It may have been deleted. Exiting program."
            sys.exit(msg)

        text = ""
        for page in reader.pages:
            text += page.extract_text()

        return text


    def _is_overhead(self, line: str) -> bool:
        """
        Check if a line of text is overhead from the psych sheet or part of an event entry.

        Keyword Arguments:
            line: line of text to check

        """
        # Check if it's an event entry
        is_event_entry = bool(re.search("en's", line))
        if is_event_entry:
            return False

        # Check if it's a country name
        is_country_name = bool(re.search("[A-Z][A-Z][A-Z] - ", line))
        return not is_country_name


    def _delete_overhead(self, lines: list[str]) -> list[str]:
        """
        Remove all overhead lines from lines.

        Keyword Arguments:
            lines: the list of lines to be filtered

        """
        filtered_lines = list(filter(lambda x: not self._is_overhead(x), lines))
        return [line.strip() for line in filtered_lines]


    def _get_entries(self, filename: str) -> list[str]:
        """Get the entries from the psych sheet."""
        pdf_text = self._get_text(filename)

        lines = pdf_text.split("\n")
        cutoff = lines.index("Entry List by NAT")
        entry_lines = lines[cutoff:]

        return self._delete_overhead(entry_lines)


    def _get_event(self, line: str) -> tuple[str, str]:
        """
        Get the event name and return it along with the rest of the line separate from it.

        Keyword Arguments:
            line: the line of text to find the event name in

        """
        try:
            cutoff = line.index("  -  ")
            other = line[:cutoff]
            event = line[cutoff + 5:]
        except ValueError:
            cutoff = line.index('"')
            other = line[:cutoff + 1]
            event = line[cutoff + 2:]

        return event, other


    def _get_height(self, text: str) -> tuple[float | None, str]:
        """
        Get the height and return it along with the rest of the line separate from it.

        Keyword Arguments:
            text: the text to find the height in

        """
        if text[-1] == '"':
            height = float(text.split()[-3])
            rest = " ".join(text.split()[:-3])
            return height, rest

        return None, text


    def _get_birthday(self, text: str) -> tuple[str, str]:
        """
        Get the birthday and name from a line of text.

        Keyword Arguments:
            text: the text to find the birthday in

        """
        birthday = " ".join(text.split()[-3:])
        name = " ".join(text.split()[:-3])
        return birthday, name


    def _get_schedule_chunks(self, schedule_url: str) -> list[str]:
        """
        Return one chunk of the schedule for each day in the meet.

        Keyword Arguments:
            schedule_url: the URL of the schedule to get

        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(schedule_url)

        print("\n1/2 - Fetching schedule from the web page...")
        time.sleep(5)  # Adjust this time if the page is taking longer to load
        lines = driver.find_elements(By.CLASS_NAME, "schedule__day")
        print("2/2 - Parsing schedule...\n")

        lines_text = [line.text for line in lines]
        driver.quit()

        return lines_text


    def _format_event_name(self, event: str) -> str:
        """
        Convert event text into same event name as on psych sheet.

        Keyword Arguments:
            event: the event name to format

        """
        partially_corrected = re.sub("m Medley", "m Individual Medley", event)
        return re.sub("en ", "en's ", partially_corrected)
