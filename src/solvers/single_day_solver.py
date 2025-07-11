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

        self.num_females: int = 0
        self.num_males: int = 0
        self.solution_values: list[float] = []

        self.forbidden_lineups: list[list[Swimmer]] = []


    def __repr__(self) -> str:
        """Return a string representation of the SingleDaySolver."""
        return f"SingleDaySolver(day={self.day}, num_females={self.num_females}, num_males={self.num_males})"


    def solve(self) -> tuple[list[Swimmer], Swimmer]:
        """Solve the mixed integer program to find the optimal lineup for the day."""
        self.solver = pywraplp.Solver.CreateSolver("SAT")
        self._get_data()
        self._get_solution()
        return self._get_optimal_lineup()


    def exclude_lineup(self, lineup: list[Swimmer], captain: Swimmer) -> None:
        """Exclude a specific lineup from being considered in the optimization."""
        if DEBUG:
            print(f"Excluding lineup: {[swimmer.name for swimmer in lineup]}")
        self.forbidden_lineups.append((lineup, captain))


    def include_lineup(self, lineup: list[Swimmer], captain: Swimmer) -> None:
        """Include a specific lineup back into consideration."""
        if DEBUG:
            print(f"Including lineup: {[swimmer.name for swimmer in lineup]}")
        # TODO: figure out if this doesn't work if a swimmer is modified after lineup is excluded and before it is included again
        if (lineup, captain) in self.forbidden_lineups:
            self.forbidden_lineups.remove((lineup, captain))


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

        female_captain_vars = []
        for index in range(self.num_females):
            var = self.solver.IntVar(0, 1, f"xc{index + 1}")
            female_captain_vars.append(var)

        male_captain_vars = []
        for index in range(self.num_males):
            var = self.solver.IntVar(0, 1, f"yc{index + 1}")
            male_captain_vars.append(var)

        # Create objective function - TODO: figure out how to factor in captain double points
        objective_terms = []
        for index, swimmer in enumerate(self.female_swimmers):
            objective_terms.append(swimmer.projected_points[self.day - 1] * (female_vars[index] + female_captain_vars[index]))
        for index, swimmer in enumerate(self.male_swimmers):
            objective_terms.append(swimmer.projected_points[self.day - 1] * (male_vars[index] + male_captain_vars[index]))

        self.solver.Maximize(sum(objective_terms))

        # Budget constraint
        budget_terms = []
        for index, swimmer in enumerate(self.female_swimmers):
            budget_terms.append(swimmer.cost * female_vars[index])
        for index, swimmer in enumerate(self.male_swimmers):
            budget_terms.append(swimmer.cost * male_vars[index])

        self.solver.Add(sum(budget_terms) <= BUDGET)

        # Forbidden lineups constraints
        for lineup, captain in self.forbidden_lineups:
            # Use names instead of Swimmer objects for checking in case entries are excluded
            lineup_names = [swimmer.name for swimmer in lineup]

            vars_in_lineup = []
            for index, swimmer in enumerate(self.female_swimmers):
                if swimmer.name in lineup_names:
                    vars_in_lineup.append(female_vars[index])
                    if swimmer.name == captain.name:
                        vars_in_lineup.append(female_captain_vars[index])
            for index, swimmer in enumerate(self.male_swimmers):
                if swimmer.name in lineup_names:
                    vars_in_lineup.append(male_vars[index])
                    if swimmer.name == captain.name:
                        vars_in_lineup.append(male_captain_vars[index])

            self.solver.Add(sum(vars_in_lineup) <= ROSTER_SIZE)

        # Number of females constraint
        self.solver.Add(sum(female_vars) == ROSTER_SIZE // 2)

        # Number of males constraint
        self.solver.Add(sum(male_vars) == ROSTER_SIZE // 2)

        # Captain constraints (can't be captain if not in lineup)
        for swimmer_var, captain_var in zip(female_vars + male_vars, female_captain_vars + male_captain_vars, strict=True):
            self.solver.Add(captain_var <= swimmer_var)
        self.solver.Add(sum(male_captain_vars + female_captain_vars) == 1)

        # Solve
        status = self.solver.Solve()

        # Check that solver worked
        if status != pywraplp.Solver.OPTIMAL:
            msg = f"Solver failed with status {status}. Exiting program."
            sys.exit(msg)

        # Get solution values
        self.solution_values = []
        for var in female_vars + male_vars:
            self.solution_values.append(var.solution_value())
        for var in female_captain_vars + male_captain_vars:
            self.solution_values.append(var.solution_value())

    def _get_optimal_lineup(self) -> tuple[list[Swimmer], Swimmer]:
        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females)))
        lineup_female = [self.female_swimmers[x] for x in indices]

        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females, self.num_females + self.num_males)))
        lineup_male = [self.male_swimmers[x - self.num_females] for x in indices]

        lineup = lineup_female + lineup_male

        num_swimmers = self.num_females + self.num_males
        captain_index = self.solution_values[num_swimmers: 2 * num_swimmers].index(1.0)

        if captain_index < self.num_females:
            captain = self.female_swimmers[captain_index]
        else:
            captain = self.male_swimmers[captain_index - self.num_females]

        total_score = self._print_lineup(lineup, captain)
        return lineup, captain, total_score


    def _print_lineup(self, lineup: list[Swimmer], captain: Swimmer) -> None:
        print(f"The optimal lineup for day {self.day} is:")
        for swimmer in lineup:
            print(f"{swimmer.name}", end="")
            if swimmer is captain:
                print(f" ({int(swimmer.projected_points[self.day - 1] * 2)}) (---------- Captain ----------)")
            else:
                print(f" ({int(swimmer.projected_points[self.day - 1])})")

        total_score = int(self.solver.Objective().Value())
        print(f"With a total score of: {total_score}")
        return total_score


    def _get_male_swimmers(self) -> list[Swimmer]:
        male_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Male" and swimmer.excluded is False]
        self.num_males = len(male_swimmers)

        return sorted(male_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)


    def _get_female_swimmers(self) -> list[Swimmer]:
        female_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Female" and swimmer.excluded is False]
        self.num_females = len(female_swimmers)

        return sorted(female_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)
