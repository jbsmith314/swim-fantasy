"""A class to solve the mixed integer program for a single day of a swim meet."""

import sys

from ortools.linear_solver import pywraplp

from swimmer import Swimmer

ROSTER_SIZE = 8
BUDGET = 200
DEBUG = False

class SingleDaySolver:
    """A class to solve the mixed integer program for a single day of the swim meet."""

    def __init__(self, swimmers: list[Swimmer], day: int) -> None:
        """Initialize the SingleDaySolver with a list of swimmers and the day of the meet."""
        self.all_swimmers = swimmers
        self.day = day

        self.solver = None
        self.male_swimmers = []
        self.female_swimmers = []
        self.female_points = []
        self.male_points = []
        self.female_costs = []
        self.male_costs = []

        self.num_females = 0
        self.num_males = 0
        self.solution_values = []

        self.forbidden_swimmers = []
        self.forbidden_lineups = []


    def __repr__(self) -> str:
        """Return a string representation of the SingleDaySolver."""
        return f"SingleDaySolver(day={self.day}, num_females={self.num_females}, num_males={self.num_males})"


    def solve(self) -> tuple[list[Swimmer], Swimmer]:
        """Solve the mixed integer program to find the optimal lineup for the day."""
        self.solver = pywraplp.Solver.CreateSolver("SAT")
        self._get_data()
        self._get_solution()
        return self._get_optimal_lineup()


    def exlude_lineup(self, lineup: list[Swimmer]) -> None:
        """Exclude a specific lineup from being considered in the optimization."""
        if DEBUG:
            print(f"Excluding lineup: {[swimmer.name for swimmer in lineup]}")
        self.forbidden_lineups.append(lineup)


    def include_lineup(self, lineup: list[Swimmer]) -> None:
        """Include a specific lineup back into consideration."""
        if DEBUG:
            print(f"Including lineup: {[swimmer.name for swimmer in lineup]}")
        if lineup in self.forbidden_lineups:
            self.forbidden_lineups.remove(lineup)


    def exclude_swimmer(self, swimmer_name: str) -> None:
        """Exclude a swimmer from the lineup."""
        for swimmer in self.all_swimmers:
            if swimmer.name == swimmer_name:
                swimmer.excluded = True
                break


    def include_swimmer(self, swimmer_name: str) -> None:
        """Include a swimmer in the lineup."""
        for swimmer in self.all_swimmers:
            if swimmer.name == swimmer_name:
                swimmer.excluded = False
                break


    def exclude_entry(self, swimmer_name: str, entry_event: str) -> None:
        """Exclude a specific entry for a swimmer."""
        for swimmer in self.all_swimmers:
            if swimmer.name == swimmer_name and entry_event in swimmer.entries:
                swimmer.entries[entry_event].excluded = True
                print(f"Excluded entry {entry_event} for swimmer {swimmer_name}.")
                swimmer.update_projected_points()
                return


    def include_entry(self, swimmer_name: str, entry_event: str) -> None:
        """Include a specific entry for a swimmer."""
        for swimmer in self.all_swimmers:
            if swimmer.name == swimmer_name and entry_event in swimmer.entries:
                swimmer.entries[entry_event].excluded = False
                print(f"Included entry {entry_event} for swimmer {swimmer_name}.")
                swimmer.update_projected_points()
                return


    def _get_data(self) -> None:
        self.male_swimmers = self._get_male_swimmers()
        self.female_swimmers = self._get_female_swimmers()
        """Get the data needed to solve the mixed integer program."""
        # female projected points from greatest to least
        self.female_points = [x.projected_points[self.day - 1] for x in self.female_swimmers]
        # male projected points from greatest to least
        self.male_points = [x.projected_points[self.day - 1] for x in self.male_swimmers]

        # female costs in same swimmer order as projected points
        self.female_costs = [x.cost for x in self.female_swimmers]
        # male costs in same swimmer order as projected points
        self.male_costs = [x.cost for x in self.male_swimmers]


    def _get_solution(self) -> None:
        # Declare decision variables for female swimmers
        female_vars = []
        for index in range(self.num_females):
            var = self.solver.IntVar(0, 1, f"x{index + 1}")
            female_vars.append(var)

        # Declare decision variables for male swimmers
        male_vars = []
        for index in range(self.num_males):
            var = self.solver.IntVar(0, 1, f"y{index + 1}")
            male_vars.append(var)

        # Create objective function
        objective_terms = []
        for index, swimmer in enumerate(self.female_swimmers):
            objective_terms.append(swimmer.projected_points[self.day - 1] * female_vars[index])
        for index, swimmer in enumerate(self.male_swimmers):
            objective_terms.append(swimmer.projected_points[self.day - 1] * male_vars[index])

        self.solver.Maximize(sum(objective_terms))

        # Budget constraint
        budget_terms = []
        for index, swimmer in enumerate(self.female_swimmers):
            budget_terms.append(swimmer.cost * female_vars[index])
        for index, swimmer in enumerate(self.male_swimmers):
            budget_terms.append(swimmer.cost * male_vars[index])

        self.solver.Add(sum(budget_terms) <= BUDGET)

        # Number of females constraint
        self.solver.Add(sum(female_vars) <= ROSTER_SIZE // 2)

        # Number of males constraint
        self.solver.Add(sum(male_vars) <= ROSTER_SIZE // 2)

        # Solve
        status = self.solver.Solve()

        # Check that solver worked
        if status != pywraplp.Solver.OPTIMAL:
            msg = f"Solver failed with status {status}. Exiting program."
            sys.exit(msg)

        # Get solution values
        self.solution_values = []
        for var in female_vars:
            self.solution_values.append(var.solution_value())
        for var in male_vars:
            self.solution_values.append(var.solution_value())


    def _get_optimal_lineup(self) -> tuple[list[Swimmer], Swimmer]:
        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females)))
        lineup_female = [self.female_swimmers[x] for x in indices]

        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females, self.num_females + self.num_males)))
        lineup_male = [self.male_swimmers[x - self.num_females] for x in indices]

        lineup = lineup_female + lineup_male
        captain = max(lineup, key=lambda x: x.projected_points[self.day - 1])

        self._print_lineup(lineup, captain)
        return lineup, captain


    def _print_lineup(self, lineup: list[Swimmer], captain: Swimmer) -> None:
        print(f"The optimal lineup for day {self.day} is:")
        for swimmer in lineup:
            print(f"{swimmer.name}", end="")
            if swimmer is captain:
                print(f" (Captain) ({int(swimmer.projected_points[self.day - 1] * 2)})")
            else:
                print(f" ({int(swimmer.projected_points[self.day - 1])})")
        print(f"With a total score of: {int(self.solver.Objective().Value() + captain.projected_points[self.day - 1])}")


    def _get_male_swimmers(self) -> list[Swimmer]:
        male_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Male" and swimmer.excluded is False]
        self.num_males = len(male_swimmers)

        return sorted(male_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)


    def _get_female_swimmers(self) -> list[Swimmer]:
        female_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Female" and swimmer.excluded is False]
        self.num_females = len(female_swimmers)

        return sorted(female_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)
