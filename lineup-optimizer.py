import sys
import re
from typing import List
from pypdf import PdfReader

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

def check_overhead(line: str) -> bool:
    """
    Check if a line of text is overhead from the psych sheet or
    part of an event entry.

        Keyword:
    """

    # Check if it's an event entry
    check1 = bool(re.search("en's", line))

    # Check if it's a country name
    check2 = bool(re.search("[A-Z][A-Z][A-Z] - ", line))

    return check1 or check2

def delete_overhead(lines: List[str]) -> List[str]:
    """
    Delete all lines
    """
    filtered_lines = filter(check_overhead, lines)

    return list(filtered_lines)

def main():
    filename = sys.argv[1]

    pdf_text = get_text(filename)
    lines = pdf_text.split('\n')
    cutoff = lines.index("Entry List by NAT")
    entry_lines = lines[cutoff:]

    stuff = delete_overhead(entry_lines)
    print(stuff)

if __name__ == "__main__":
    main()