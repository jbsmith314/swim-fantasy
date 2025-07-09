"""
Get world records from online.

To Do:
Spell out circumstances - Legend:
# -> Record awaiting ratification by FINA;
h -> heat;
sf -> semifinal;
r -> relay 1st leg;
rh -> relay heat 1st leg;
b -> B final;
† -> en route to final mark;
tt -> time trial
"""

import sqlite3

import requests
from bs4 import BeautifulSoup

EXPECTED_COLS = 9
MINIMUM_TIME_LENGTH = 5

def add_to_db(rows: list[dict]) -> None:
    """Add world records to the database."""
    conn = sqlite3.connect("swimming.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_records (
            id INTEGER PRIMARY KEY,
            sex TEXT,
            stroke TEXT,
            distance TEXT,
            course TEXT,
            time TEXT,
            swimmer TEXT,
            country TEXT,
            date TEXT,
            meet TEXT,
            location TEXT,
            awaiting_ratification BOOLEAN,
            heat BOOLEAN,
            semifinal BOOLEAN,
            relay BOOLEAN,
            b_final BOOLEAN,
            race_split BOOLEAN,
            time_trial BOOLEAN
        )
    """)

    for row in rows:
        cursor.execute("""
            INSERT INTO world_records (sex, stroke, distance, course, time, swimmer, country, date, meet, location, awaiting_ratification, heat, semifinal, relay, b_final, race_split, time_trial)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["sex"],
            row["stroke"],
            row["distance"],
            row["course"],
            row["time"],
            row["swimmer"],
            row["country"],
            row["date"],
            row["meet"],
            row["location"],
            row["awaiting_ratification"],
            row["heat"],
            row["semifinal"],
            row["relay"],
            row["b_final"],
            row["race_split"],
            row["time_trial"],
        ))

    print(f"Added {len(rows)} world records to the database.")
    conn.commit()
    conn.close()

def get_wr_pages() -> list[str]:
    """Get world record pages from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/Category:World_record_progressions_in_swimming"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    records = soup.find_all("a", title=lambda x: x and "metres" in x and "relay" not in x)

    return [f"https://en.wikipedia.org/{record['href']}" for record in records]


def get_wrs(url: str) -> list[dict]:
    """Get world records from a specific page."""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    records = soup.find_all("table", class_="wikitable")

    is_100_im = "100_metres_individual_medley" in url

    # there is no LCM 100 IM, so there are only 2 tables to scrape for that URL
    num_tables = 2 if is_100_im else 4

    # filter out tables for old regulations and cut to only world record tables
    records = [table for table in records if not table.find_previous("h4") or "old regulations" not in table.find_previous("h4").text.lower()][:num_tables]

    rows = []
    for table in records:
        sex = table.find_previous("h2").text.strip() if not is_100_im else table.find_previous("h3").text.strip()
        course = {"Long course": "LCM", "Short course": "SCM", "Short course (25m)": "SCM"}.get(table.find_previous("h3").text.strip() if not is_100_im else table.find_previous("h2").text.strip(), "Unknown Course")
        event = table.find_previous("h1").text.strip().replace("World record progression ", "")
        stroke = " ".join([word[0].upper() + word[1:] for word in event.split(" ")[2:]])
        distance = event.split(" ")[0]

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) == EXPECTED_COLS - 2 and len(cols[0].text.strip()) >= MINIMUM_TIME_LENGTH: # Add # column if missing (for end of men's 200 IM)
                cols = [None, *cols]
            adjust = False
            if len(cols) == EXPECTED_COLS - 3:
                cols = [None, cols[0], None, *cols[1:], None]  # Add empty columns for missing #, circumstance, and reference for 200 IM long course
            if len(cols) == EXPECTED_COLS - 2:
                adjust = True
                cols = [*cols[:2], None, cols[2], None, *cols[3:]]
            if len(cols) == EXPECTED_COLS - 1:
                cols = [*cols[:2], None, *cols[2:]]  # Add empty column for circumstance if missing
            _, time, circumstance, swimmer, country, date, meet, location, _ = [col.text.strip() if col else "" for col in cols]
            if adjust:
                time = time[:len(time) // 2] # Remove duplicate time
                swimmer = swimmer[len(swimmer) // 2 + 1:] # Remove duplicate swimmer name
                country = row.find("span", class_="flagicon").find("a")["title"] # Convert flag icon to country name

            meet = "Unknown" if meet in ["-", "?"] else meet

            if swimmer == "?":
                continue

            circumstances = [x.strip() for x in circumstance.split(",")]
            awaiting_ratification = "#" in circumstances
            heat = "h" in circumstances or "rh" in circumstances
            semifinal = "sf" in circumstances
            relay = "r" in circumstances or "rh" in circumstances
            b_final = "b" in circumstances
            race_split = "†" in circumstances
            time_trial = "tt" in circumstances

            row_data = {
                "sex": sex,
                "stroke": stroke,
                "distance": distance,
                "course": course,
                "time": time,
                "swimmer": swimmer,
                "country": country,
                "date": date,
                "meet": meet,
                "location": location,
                "awaiting_ratification": awaiting_ratification,
                "heat": heat,
                "semifinal": semifinal,
                "relay": relay,
                "b_final": b_final,
                "race_split": race_split,
                "time_trial": time_trial,
            }
            rows.append(row_data)

    return rows


def main() -> None:
    """Get world records."""
    wr_pages = get_wr_pages()
    wrs = []
    for url in wr_pages:  # Limit to first two pages for testing
        wrs.extend(get_wrs(url))

    print(f"World records found: {len(wrs)}")

    add_to_db(wrs)

if __name__ == "__main__":
    main()
