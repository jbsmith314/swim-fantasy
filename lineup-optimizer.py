import sys
import re
from typing import List
from pypdf import PdfReader
import os

class Swimmer:
    """
    Holds all the information for a swimmer entered in the meet.
    """
    def __init__(self, name, country, entries, birthday, height):
        self.name = name
        self.country = country
        self.entries = entries
        self.birthday = birthday
        self.height = height
    
    def add_event(self, entry):
        self.entries = self.entries.append(entry)

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
    clean_lines = map(lambda x: x.strip(), filtered_lines)

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


def main():
    if not valid_input():
        file_name = os.path.basename(__file__)
        print(f"Example use: python {file_name} PsychSheets\\2024-scm-worlds-psych-sheet.pdf\n")
        return

    filename = sys.argv[1]

    pdf_text = get_text(filename)
    lines = pdf_text.split("\n")
    cutoff = lines.index("Entry List by NAT")
    entry_lines = lines[cutoff:]

    filtered_lines = delete_overhead(entry_lines)
    for line in filtered_lines:
        print(line)


if __name__ == "__main__":
    main()
