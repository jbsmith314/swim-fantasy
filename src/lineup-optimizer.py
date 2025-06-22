"""The main script to run the lineup optimizer for the World Aquatics Swimming Championships Fantasy Game."""

import sys

from data_parser import DataParser
from single_day_solver import SingleDaySolver

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
    schedule = parser.get_schedule(SCHEDULE_URL)
    swimmers = parser.get_swimmers(psych_sheet_filename)
    parser.update_seeds(swimmers)
    parser.update_projected_points(swimmers, base_times, schedule)

    solver = SingleDaySolver(swimmers, DAY)
    solver.get_data()
    solver.solve()


if __name__ == "__main__":
    main()
