"""The main script to run the lineup optimizer for the World Aquatics Swimming Championships Fantasy Game."""

import json
import sys
from pathlib import Path

from data_parser import DataParser
from single_day_solver import SingleDaySolver

# TODO: SCHEDULE_URL needs to change for each meet
SCHEDULE_URL = "https://www.worldaquatics.com/competitions/3433/world-aquatics-swimming-championships-25m-2024/schedule?phase=All"
NUM_EXPECTED_ARGS = 3
DAY = 5
CACHE_FILE_PATH = Path(__file__).parent.parent.resolve() / "cached_data.json"

def check_valid_input() -> bool:
    """Check valid command line input to run the program."""
    if len(sys.argv) != NUM_EXPECTED_ARGS:
        sys.exit("This program takes two additional arguments.\nExample input: uv run .\\src\\lineup-optimizer.py .\\PsychSheets\\2024-scm-worlds-psych-sheet.pdf .\\BaseTimes\\2023-2024-scm-base-times.pdf")

    psych_sheet = sys.argv[1]
    if psych_sheet[-4:] != ".pdf":
        sys.exit("Psych sheet file must be a PDF.\nExample input: uv run .\\src\\lineup-optimizer.py .\\PsychSheets\\2024-scm-worlds-psych-sheet.pdf .\\BaseTimes\\2023-2024-scm-base-times.pdf")

    base_times = sys.argv[2]
    if base_times[-4:] != ".pdf":
        sys.exit("Base times file must be a PDF.\nExample input: uv run .\\src\\lineup-optimizer.py .\\PsychSheets\\2024-scm-worlds-psych-sheet.pdf .\\BaseTimes\\2023-2024-scm-base-times.pdf")

    return True


def main() -> None:
    """Run the lineup optimizer."""
    check_valid_input()

    psych_sheet_filename = sys.argv[1]
    base_times_filename = sys.argv[2]

    parser = DataParser()
    parser.get_all_data()

    try:
        with CACHE_FILE_PATH.open("r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Cache file not found. Creating a new cache file.")
        data = {}

    # ------------------------- Get schedule -------------------------

    # If the schedule URL matches the cached one, use the cached schedule, otherwise, fetch a new schedule
    if data.get("schedule_data", {}).get("schedule_url", "") == SCHEDULE_URL:
        print("Using cached schedule.")
        # Get cached schedule
        string_keys_schedule = data.get("schedule_data", {}).get("schedule", {})
        # Convert string keys to integers for the schedule
        parser.schedule = {int(k): v for k, v in string_keys_schedule.items()}
    else:
        if data.get("schedule_data", {}).get("schedule_url", ""):
            print("Schedule URL has changed. Fetching new schedule.")
        else:
            print("No cached schedule found. Fetching new schedule.")

        parser.get_schedule(SCHEDULE_URL)

    # ---------------------------------------- Get base times ----------------------------------------

    # If the base times filename matches the cached one, use the cached base times, otherwise, fetch new base times
    if data.get("base_times_data", {}).get("base_times_filename", "") == base_times_filename:
        print("Using cached base times.")
        # Get cached base times
        parser.base_times = data.get("base_times_data", {}).get("base_times", {})
    else:
        if data.get("base_times_data", {}).get("base_times_filename", ""):
            print("Base times filename has changed. Extracting new base times.")
        else:
            print("No cached base times found. Extracting new base times.")

        parser.get_base_times(base_times_filename)

    # -------------------------------- Update cache file --------------------------------
    with CACHE_FILE_PATH.open("w") as json_file:
        schedule_data = {
            "schedule_data": {
                "schedule": parser.schedule,
                "schedule_url": SCHEDULE_URL,
            },
            "base_times_data": {
                "base_times_filename": base_times_filename,
                "base_times": parser.base_times,
            },
        }
        json.dump(schedule_data, json_file)

    # ------------------------------------------------------------------------------------------------

    parser.create_swimmers(psych_sheet_filename)
    parser.update_seeds()
    parser.update_projected_points()

    # ------------------------- Solve the optimal lineup for the day -------------------------

    solver = SingleDaySolver(parser.swimmers, DAY)
    solver.exclude_swimmer("KORSTANJE Nyls")
    solver.solve()
    solver.exclude_entry("PONTI Noe", "Men's 100m Butterfly")
    solver.solve()


if __name__ == "__main__":
    main()
