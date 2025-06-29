"""The main script to run the lineup optimizer for the World Aquatics Swimming Championships Fantasy Game."""

import sys

from data_parser import DataParser
from full_meet_solver import FullMeetSolver
from single_day_solver import SingleDaySolver

NUM_EXPECTED_ARGS = 3 # Expected number of command line arguments
DAY = 5 # Day for the single day solver to solve for
NUM_DAYS = 6 # Number of days in the meet
NUM_LINEUPS = 1 # Number of lineups to generate for the single day solver

CREDITS = 800
ADDITIONAL_CREDITS = 150
SWITCH_COST = 1
SWITCHES = (CREDITS + ADDITIONAL_CREDITS) // SWITCH_COST

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


def test_single_day_solver(parser: DataParser) -> None:
    """Test the single day solver."""
    for day in range(6):
        solver = SingleDaySolver(parser.swimmers, day + 1)

        # number larger than any possible score
        prev_score = 99999

        # get the NUM_LINEUPS top lineups
        for i in range(NUM_LINEUPS):
            # TODO: use NextSolution method
            print(f"\nSolving for lineup {i + 1}...")
            lineup, captain, curr_score = solver.solve()
            if i > 0 and curr_score > prev_score:
                sys.exit("Optimal lineup score decreased, so something is wrong. Stopping early.")
            prev_score = curr_score


def test_full_meet_solver(parser: DataParser) -> None:
    """Test the full meet solver."""
    for num_days in range(1, NUM_DAYS + 1):
        for day in range(NUM_DAYS - num_days + 1):
            solver = FullMeetSolver(parser.swimmers, SWITCHES, day + 1, day + num_days)
            solver.solve()


def main() -> None:
    """Run the lineup optimizer."""
    check_valid_input()

    # parse data from schedule, psych sheet, and base times
    parser = DataParser()
    parser.get_all_data()
    parser.create_swimmers()
    parser.update_seeds()
    parser.update_projected_points()

    test_full_meet_solver(parser)


if __name__ == "__main__":
    main()
