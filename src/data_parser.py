import re
import time
from swimmer import Swimmer
from pypdf import PdfReader
from typing import Dict, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        Get the event name and return it along with the rest of the line separate from it.

            Keyword arguments:
            line: the line of text to find the event name in

        Return the event name and rest of the text
        """
        try:
            cutoff = line.index("  -  ")
            other = line[:cutoff]
            event = line[cutoff + 5:]
        except Exception:
            cutoff = line.index('"')
            other = line[:cutoff + 1]
            event = line[cutoff + 2:]

        return event, other


    def get_height(self, text: str) -> Tuple[float, str]:
        """
        Get the height and return it along with the rest of the line separate from it.

            Keyword arguments:
            text: the text to find the height in

        Return the height if found, and None if it's not found,
        along with the rest of the text
        """
        if text[-1] == '"':
            height = float(text.split()[-3])
            rest = " ".join(text.split()[:-3])
            return height, rest
        else:
            return None, text


    def get_birthday(self, text: str) -> Tuple[str, str]:
        """
        Get the birthday and name from a line of text.

            Keyword arguments:
            text: the text to find the birthday in

        Return the birthday and swimmer name
        """
        birthday = " ".join(text.split()[-3:])
        name = " ".join(text.split()[:-3])
        return birthday, name


    def update_seeds(self, swimmers: List[Swimmer]):
        """
        Update the seeds for all swimmers.

            Keyword arguments:
            swimmers: the swimmers to iterate through
        """
        for swimmer in swimmers:
            swimmer.update_seeds(swimmers)


    def update_projected_points(self, swimmers: List[Swimmer], base_times: Dict, schedule: Dict):
        """
        Update the projected points for all swimmers.

            Keyword arguments:
            swimmers: the swimmers to iterate through
        """
        for swimmer in swimmers:
            swimmer.update_projected_points(base_times, schedule)


    def get_schedule_chunks(self, schedule_url: str) -> List[str]:
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(schedule_url)

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


    def get_schedule(self, schedule_url: str) -> Dict:
        chunks = self.get_schedule_chunks(schedule_url)
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