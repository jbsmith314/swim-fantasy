"""The main script to run the lineup optimizer for the World Aquatics Swimming Championships Fantasy Game."""

import sys

from data_parser import DataParser
from solvers.full_meet_solver import FullMeetSolver
from solvers.single_day_solver import SingleDaySolver
from utils.constants import (
    NUM_DAYS,
    NUM_EXPECTED_ARGS,
    NUM_LINEUPS,
    SCHEDULE_URLS,
    SWITCHES,
)


def check_valid_input() -> None:
    """Check valid command line input to run the program."""
    if len(sys.argv) != NUM_EXPECTED_ARGS:
        sys.exit(f'This program takes two additional arguments.\nExample input: uv run .\\src\\{__file__} "2024 SCM Worlds"')

    if sys.argv[1] not in SCHEDULE_URLS:
        print("Meet not recognized. Please use one of the following:")
        for url in SCHEDULE_URLS:
            print(url)
        sys.exit()


def test_single_day_solver(parser: DataParser) -> None:
    """Test the single day solver."""
    print(len(parser.schedule))
    for day in range(len(parser.schedule)):
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

    # Takes about 2 seconds
    parser.create_swimmers()

    parser.update_seeds()
    parser.update_projected_points()

    # Takes majority of time
    # test_full_meet_solver(parser)
    test_single_day_solver(parser)

if __name__ == "__main__":
    main()
