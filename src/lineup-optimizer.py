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

def check_valid_input() -> bool:
    """Check valid command line input to run the program."""
    if len(sys.argv) != NUM_EXPECTED_ARGS:
        sys.exit("This program takes two additional arguments.\nExample input: uv run .\\src\\lineup-optimizer.py .\\PsychSheets\\2024-scm-worlds-psych-sheet.pdf .\\BaseTimes\\2023-2024-scm-base-times.pdf")

    psych_sheet = sys.argv[1]
    if psych_sheet[-4:] != ".pdf":
        sys.exit("Psych sheet file must be a PDF.")

    base_times = sys.argv[2]
    if base_times[-4:] != ".pdf":
        sys.exit("Base times file must be a PDF.")

    return True


def main() -> None:
    """Run the lineup optimizer."""
    check_valid_input()

    psych_sheet_filename = sys.argv[1]
    base_times_filename = sys.argv[2]

    parser = DataParser()
    base_times = parser.get_base_times(base_times_filename)

    # ------------------------- Get schedule -------------------------

    with Path("schedule.json").open("r") as file:
        data = json.load(file)

    # If the schedule URL matches the cached one, use the cached schedule
    # Otherwise, fetch a new schedule
    if data.get("schedule_url", "") == SCHEDULE_URL:
        print("Using cached schedule.")
        # Convert string keys to integers for the schedule
        string_keys_schedule = data.get("schedule", {})
        parser.schedule = {int(k): v for k, v in string_keys_schedule.items()}
    else:
        if data.get("schedule_url", ""):
            print("Schedule URL has changed. Fetching new schedule.")
        else:
            print("No cached schedule found. Fetching new schedule.")

        parser.get_schedule(SCHEDULE_URL)

        with Path("schedule.json").open("w") as json_file:
            schedule_data = {
                "schedule": parser.schedule,
                "schedule_url": SCHEDULE_URL,
            }
            json.dump(schedule_data, json_file)

    print(parser.schedule)

    # ------------------------------------------------------------------

    swimmers = parser.get_swimmers(psych_sheet_filename)
    parser.update_seeds(swimmers)
    parser.update_projected_points()

    solver = SingleDaySolver(swimmers, DAY)
    solver.exclude_swimmer("KORSTANJE Nyls")
    solver.solve()
    solver.exclude_entry("PONTI Noe", "Men's 100m Butterfly")
    solver.solve()


if __name__ == "__main__":
    main()
