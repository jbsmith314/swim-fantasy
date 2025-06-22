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
        self.day = day
        self.solver = None
        self.male_swimmers = self._get_male_swimmers(swimmers)
        self.female_swimmers = self._get_female_swimmers(swimmers)
        self.female_points = []
        self.male_points = []
        self.female_costs = []
        self.male_costs = []

        self.num_females = len(self.female_swimmers)
        self.num_males = len(self.male_swimmers)
        self.solution_values = []


    def __repr__(self) -> str:
        """Return a string representation of the SingleDaySolver."""
        return f"SingleDaySolver(day={self.day}, num_females={self.num_females}, num_males={self.num_males})"


    def get_data(self) -> None:
        """Get the data needed to solve the mixed integer program."""
        # female projected points from greatest to least
        self.female_points = [x.projected_points[self.day - 1] for x in self.female_swimmers]
        # male projected points from greatest to least
        self.male_points = [x.projected_points[self.day - 1] for x in self.male_swimmers]

        # female costs in same swimmer order as projected points
        self.female_costs = [x.cost for x in self.female_swimmers]
        # male costs in same swimmer order as projected points
        self.male_costs = [x.cost for x in self.male_swimmers]


    def solve(self) -> None:
        """Solve the mixed integer program to find the optimal lineup for the day."""
        self.solver = pywraplp.Solver.CreateSolver("SAT")
        self._get_solution()

        optimal_lineup, captain = self._get_optimal_lineup()
        print("The optimal lineup is:")
        self._print_lineup(optimal_lineup, captain)
        print(f"With a total score of: {int(self.solver.Objective().Value() + captain.projected_points[self.day - 1])}")


    def _get_optimal_lineup(self) -> tuple[list[Swimmer], Swimmer]:
        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females)))
        lineup_female = [self.female_swimmers[x] for x in indices]

        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females, self.num_females + self.num_males)))
        lineup_male = [self.male_swimmers[x - self.num_females] for x in indices]

        lineup = lineup_female + lineup_male
        captain = max(lineup, key=lambda x: x.projected_points[self.day - 1])

        return lineup, captain

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
        print(f"Solving with {self.solver.SolverVersion()}")
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


    def _print_lineup(self, lineup: list[Swimmer], captain: Swimmer) -> None:
        for swimmer in lineup:
            print(f"{swimmer.name}", end="")
            if swimmer is captain:
                print(f" (Captain) ({int(swimmer.projected_points[self.day - 1] * 2)})", end="")
            else:
                print(f" ({int(swimmer.projected_points[self.day - 1])})", end="")
            print()


    def _get_male_swimmers(self, swimmers: list[Swimmer]) -> list[Swimmer]:
        male_swimmers = [swimmer for swimmer in swimmers if swimmer.sex == "Male"]

        return sorted(male_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)


    def _get_female_swimmers(self, swimmers: list[Swimmer]) -> list[Swimmer]:
        female_swimmers = [swimmer for swimmer in swimmers if swimmer.sex == "Female"]

        return sorted(female_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)
