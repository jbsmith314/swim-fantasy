"""The main script to run the lineup optimizer for the World Aquatics Swimming Championships Fantasy Game."""

import sys

from data_parser import DataParser
from single_day_solver import SingleDaySolver

NUM_EXPECTED_ARGS = 3
DAY = 5
NUM_LINEUPS = 25

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

    # parse data from schedule, psych sheet, and base times
    parser = DataParser()
    parser.get_all_data()
    parser.create_swimmers()
    parser.update_seeds()
    parser.update_projected_points()

    # solve for the top optimal lineups for the given day
    solver = SingleDaySolver(parser.swimmers, DAY)
    prev_score = 99999
    for i in range(NUM_LINEUPS):
        print(f"\nSolving for lineup {i + 1}...")
        lineup, captain, curr_score = solver.solve()
        solver.exclude_lineup(lineup, captain)
        if i > 0 and curr_score > prev_score:
            sys.exit("Optimal lineup score decreased, so something is wrong. Stopping early.")
        prev_score = curr_score


if __name__ == "__main__":
    main()
