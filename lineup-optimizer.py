import sys
import re
from typing import List, Tuple
from pypdf import PdfReader
import os

class Swimmer:
    """
    Holds all the information for a swimmer entered in the meet.
    """
    def __init__(self, name: str, country: str, birthday: str, height: float = None):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.height = height
        self.entries = {}
        self.seeds = {}
    
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
        self.entries[event] = round(time, 2)
    
    def update_seeds(self, swimmers):
        for event in self.entries.keys():
            seed = 1
            for swimmer in swimmers:
                if event in swimmer.entries and swimmer.entries[event] < self.entries[event]:
                    seed += 1
            self.seeds[event] = seed


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


def valid_input() -> bool:
    """
    Checks valid command line input to run the program.

    Returns if the input is valid
    """
    if len(sys.argv) != 2:
        print("\nERROR: takes one additional argument")
        return False

    filename = sys.argv[1]
    if filename[-4:] != ".pdf":
        print("\nERROR: file must be a pdf")
        return False

    return True


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
    rest = " ".join(text.split()[:-3])
    return birthday, rest


def get_name(text: str) -> str:
    return text


def get_swimmers(lines: List[str]) -> List[Swimmer]:
    """
    Get a list of swimmers and their events
    """
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
            birthday, rest = get_birthday(rest)
            name = get_name(rest)
            new_swimmer = Swimmer(name, country, birthday, height)
            new_swimmer.add_event(event)
            swimmers.append(new_swimmer)
    
    return swimmers

def update_seeds(swimmers: List[Swimmer]):
    for swimmer in swimmers:
        swimmer.update_seeds(swimmers)

def main():
    if not valid_input():
        filename = os.path.basename(__file__)
        print(f"Example use: python {filename} PsychSheets\\2024-scm-worlds-psych-sheet.pdf\n")
        return

    lines = get_entries()
    swimmers = get_swimmers(lines)
    update_seeds(swimmers)
    for swimmer in swimmers[:100]:
        print(swimmer.name, swimmer.seeds)

if __name__ == "__main__":
    main()
