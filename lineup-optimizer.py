import sys
from data_parser import DataParser
from single_day_solver import SingleDaySolver

SCHEDULE_URL = "https://www.worldaquatics.com/competitions/3433/world-aquatics-swimming-championships-25m-2024/schedule?phase=All"

def check_valid_input() -> bool:
    """
    Checks valid command line input to run the program.

    Returns if the input is valid
    """
    if len(sys.argv) != 3:
        raise Exception("takes two additional arguments")

    psych_sheet = sys.argv[1]
    if psych_sheet[-4:] != ".pdf":
        raise Exception("psych sheet file must be a pdf")
    
    base_times = sys.argv[2]
    if base_times[-4:] != ".pdf":
        raise Exception("base times file must be a pdf")

    return True


def main():
    check_valid_input()

    psych_sheet_filename = sys.argv[1]
    base_times_filename = sys.argv[2]
    parser = DataParser()
    base_times = parser.get_base_times(base_times_filename)
    schedule = parser.get_schedule(SCHEDULE_URL)
    swimmers = parser.get_swimmers(psych_sheet_filename)
    parser.update_seeds(swimmers)
    parser.update_projected_points(swimmers, base_times, schedule)

    solver = SingleDaySolver(swimmers, 1)
    solver.get_data()
    solver.solve()


if __name__ == "__main__":
    main()
