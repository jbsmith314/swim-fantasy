"""Get world records from online."""

import datetime
import re
import sqlite3
import time

import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup

EXPECTED_COLS = 9
MINIMUM_TIME_LENGTH = 5
MAXIMUM_TIME_LENGTH = 8
EXPECTED_DATE_TOKENS = 3  # day, month, year
SECONDS_PER_MINUTE = 60

def add_to_db(rows: list[dict]) -> None:
    """Add world records to the database."""
    conn = sqlite3.connect("swimming.db")
    cursor = conn.cursor()

    cursor.execute("""DROP TABLE IF EXISTS world_records""")
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
            time_trial BOOLEAN,
            raw_circumstances TEXT,
            date_num INTEGER,
            time_in_seconds REAL
        )
    """)

    for row in rows:
        cursor.execute("""
            INSERT INTO world_records (sex, stroke, distance, course, time, swimmer, country, date, meet, location, awaiting_ratification, heat, semifinal, relay, b_final, race_split, time_trial, raw_circumstances, date_num, time_in_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            row["raw_circumstances"],
            row["date_num"],
            row["time_in_seconds"],
        ))

    print(f"Added {len(rows)} world records to database.")
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

            meet = "Unknown" if meet in ["-", "?", "–", ""] else meet # Third character is en dash, not a hyphen

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

            # Missing yd (800 free), [a], [b], [c], [d] (all 200 breast), [A] (400 free), = (equaled previous WR), [2] (Peter Williams 50 free), and * (Bernard 100 free) for circumstances

            if "," in date:
                month, day, year = date.replace(",", "").split(" ")
                date = f"{day} {month} {year}"
            else:
                day, month, year = date.split(" ")

            month_to_num = {
                "Jan": "01",
                "January": "01",
                "Feb": "02",
                "February": "02",
                "Mar": "03",
                "March": "03",
                "Apr": "04",
                "April": "04",
                "May": "05",
                "Jun": "06",
                "June": "06",
                "Jul": "07",
                "July": "07",
                "Aug": "08",
                "August": "08",
                "Sep": "09",
                "September": "09",
                "Oct": "10",
                "October": "10",
                "Nov": "11",
                "November": "11",
                "Dec": "12",
                "December": "12",
            }

            date_num = int(year) * 10000 + int(month_to_num[month]) * 100 + int(day)

            if len(time) == 0:
                time_in_seconds = 0

            # TODO: deal with = after the time
            accurate_time = (time + "0" if time[-2] == "." else time).rstrip("= ")
            if len(accurate_time) == MINIMUM_TIME_LENGTH:
                seconds, hundreths = accurate_time.split(".")
                time_in_seconds = int(seconds) + int(hundreths) / 100
            elif len(accurate_time) in [MAXIMUM_TIME_LENGTH - 1, MAXIMUM_TIME_LENGTH]:
                minutes, seconds, hundreths = re.split("[:.]", accurate_time)
                time_in_seconds = int(minutes) * 60 + int(seconds) + int(hundreths) / 100
            elif len(time) > 0:
                msg = f"Unexpected time format: {time} (length: {len(time)})"
                raise ValueError(msg)

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
                "raw_circumstances": circumstance,
                "date_num": date_num,
                "time_in_seconds": time_in_seconds,
            }
            rows.append(row_data)

    return rows


def update_db() -> None:
    """Get world records."""
    print("Fetching world records...\n")
    start = time.time()

    wr_pages = get_wr_pages()
    wrs = []
    for url in wr_pages:  # Limit to first two pages for testing
        url_start_len = len("https://en.wikipedia.org//wiki/World_record_progression_")
        print(f"Fetching records for {" ".join(url[url_start_len:].split('_')).replace('metres', 'meter')}...")
        wrs.extend(get_wrs(url))

    end = time.time()
    print(f"\nFetched {len(wrs)} world records in {end - start:.2f} seconds.")

    add_to_db(wrs)


def wr_counts_by_year() -> None:
    """Get world record counts by year."""
    conn = sqlite3.connect("swimming.db")
    cursor = conn.cursor()

    wr_counts = []
    for year in range(2000, 2025):
        cursor.execute(f"""SELECT
                        COUNT(*)
                        FROM world_records
                        WHERE
                            date_num >= {year}0101 AND
                            date_num <= {year}1231 AND
                        course = 'LCM'""")
        count = cursor.fetchone()[0]
        wr_counts.append(count)

    for count in wr_counts:
        print(count)

    conn.close()

    # plot results
    start_year = 2000
    end_year = 2024
    x_data = range(start_year, end_year + 1)
    y_data = wr_counts
    plt.plot(x_data, y_data)
    plt.xlabel("Year")
    plt.ylabel("World Record Count")
    plt.title(f"LCM World Record Counts ({start_year}-{end_year})")
    plt.show()


def seconds_to_time_str(seconds: float) -> str:
    """Convert seconds to time string."""
    if seconds >= SECONDS_PER_MINUTE:
        minutes = int(seconds // SECONDS_PER_MINUTE)
        seconds = seconds % SECONDS_PER_MINUTE
        return f"{minutes}:{seconds:05.2f}"

    return f"{seconds:05.2f}"


def get_base_times(year: int, course: str) -> dict[str, float]:
    """Get base times for each event for a given year."""
    conn = sqlite3.connect("swimming.db")
    cursor = conn.cursor()

    if course not in ["LCM", "SCM"]:
        msg = f"Unexpected course: {course}"
        raise ValueError(msg)

    month = "08"
    adjusted_year = year
    if course == "LCM":
        month = "12"
        adjusted_year -= 1

    today = datetime.datetime.now(tz=datetime.UTC).date()
    if today.year * 10000 + today.month * 100 + today.day < adjusted_year * 10000 + int(month) * 100 + 31:
        msg = f"The {year} {course} base times are not available yet. They will be available after {adjusted_year}-{month}-31."
        raise ValueError(msg)

    base_times = {}
    cursor.execute(f"""SELECT
                    sex,
                    stroke,
                    distance,
                    MIN(time_in_seconds)
                    FROM world_records
                    WHERE
                        date_num <= {adjusted_year}{month}31 AND
                    course = '{course}'
                    GROUP BY sex, stroke, distance""")
    results = cursor.fetchall()
    for sex, stroke, distance, time_in_seconds in results:
        event = f"{sex}'s {distance}m {stroke}"
        base_times[event] = time_in_seconds

    conn.close()
    return base_times


def main() -> None:
    """Control flow of program."""
    # update_db()

    # wr_counts_by_year()

    get_base_times(2026, "SCM")

if __name__ == "__main__":
    main()
