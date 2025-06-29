"""A class to solve the mixed integer program for a single day of a swim meet."""

import sys

from ortools.linear_solver import pywraplp

from swimmer import Swimmer

ROSTER_SIZE = 8
BUDGET = 200

class FullMeetSolver:
    """A class to solve the mixed integer program for the full swim meet."""

    def __init__(self, swimmers: list[Swimmer], switches: int, start_day: int = 1, end_day: int | None = None) -> None:
        """Initialize the FullMeetSolver with a list of swimmers."""
        self.all_swimmers: list[Swimmer] = swimmers
        self.switches = switches
        self.num_days: int = len(swimmers[0].projected_points)

        self.start_day, self.end_day = self._check_valid_day_range(start_day, end_day)

        self.solver = None
        self.female_swimmers: list[Swimmer] = []
        self.male_swimmers: list[Swimmer] = []

        self.female_points: list[list[float]] = [[] for _ in range(self.num_days)]
        self.male_points: list[list[float]] = [[] for _ in range(self.num_days)]
        self.female_costs: list[int] = []
        self.male_costs: list[int] = []

        self.num_females: int = 0
        self.num_males: int = 0
        self.solution_values: list[float] = []


    def __repr__(self) -> str:
        """Return a string representation of the FullMeetSolver."""
        return f"FullMeetSolver(num_females={self.num_females}, num_males={self.num_males}) from day {self.start_day} to day {self.end_day}"


    def solve(self) -> None:
        """Solve the mixed integer program to find the optimal lineups for the whole meet."""
        self.solver = pywraplp.Solver.CreateSolver("SAT")

        self._get_data()
        self._get_solution()
        self._print_solution()


    def _check_valid_day_range(self, start_day: int, end_day: int) -> tuple[int, int]:
        if start_day < 1 or start_day > self.num_days:
            msg = f"Start day must be between 1 and the number of days ({self.num_days}), inclusive."
            raise ValueError(msg)
        if end_day is not None and (end_day < start_day or end_day > self.num_days):
            msg = f"End day must be between start day ({start_day}) and the number of days ({self.num_days})."
            raise ValueError(msg)

        if end_day:
            return start_day, end_day

        return start_day, self.num_days


    def _get_data(self) -> None:
        self.male_swimmers = self._get_male_swimmers()
        self.female_swimmers = self._get_female_swimmers()
        """Get the data needed to solve the mixed integer program."""

        for day in range(self.start_day, self.end_day + 1):
            # female projected points from greatest to least
            self.female_points[day - self.start_day] = [x.projected_points[day - 1] for x in self.female_swimmers]
            # male projected points from greatest to least
            self.male_points[day - self.start_day] = [x.projected_points[day - 1] for x in self.male_swimmers]

        # female costs in same swimmer order as projected points
        self.female_costs = [x.cost for x in self.female_swimmers]
        # male costs in same swimmer order as projected points
        self.male_costs = [x.cost for x in self.male_swimmers]


    def _get_solution(self) -> None:
        # Declare decision variables for female swimmers
        female_vars = []
        for day in range(self.start_day, self.end_day + 1):
            day_vars = []
            for index in range(self.num_females):
                var = self.solver.BoolVar(f"day_{day}_female_{index + 1}")
                day_vars.append(var)
            female_vars.append(day_vars)

        # Declare decision variables for male swimmers
        male_vars = []
        for day in range(self.start_day, self.end_day + 1):
            day_vars = []
            for index in range(self.num_males):
                var = self.solver.BoolVar(f"day_{day}_male_{index + 1}")
                day_vars.append(var)
            male_vars.append(day_vars)

        # Declare decision variables for female captains
        female_captain_vars = []
        for day in range(self.start_day, self.end_day + 1):
            day_vars = []
            for index in range(self.num_females):
                var = self.solver.BoolVar(f"day_{day}_female_captain_{index + 1}")
                day_vars.append(var)
            female_captain_vars.append(day_vars)

        # Declare decision variables for male captains
        male_captain_vars = []
        for day in range(self.start_day, self.end_day + 1):
            day_vars = []
            for index in range(self.num_males):
                var = self.solver.BoolVar(f"day_{day}_male_captain_{index + 1}")
                day_vars.append(var)
            male_captain_vars.append(day_vars)

        # Declare decision variables for switches
        switch_vars = []
        for day in range(self.start_day + 1, self.end_day + 1):
            day_vars = []
            for index in range(self.num_females):
                var = self.solver.BoolVar(f"day_{day}_switch_female_{index + 1}")
                day_vars.append(var)
            for index in range(self.num_males):
                var = self.solver.BoolVar(f"day_{day}_switch_male_{index + 1}")
                day_vars.append(var)
            switch_vars.append(day_vars)

        # Declare fake decision variables for number of switches per day to make constraints easier
        # Can be up to ROSTER_SIZE * 2 switches per day because switches are double counted
        day_switch_counts = []
        for day in range(self.start_day + 1, self.end_day + 1):
            var = self.solver.IntVar(0, ROSTER_SIZE * 2, f"day_{day}_num_switches")
            day_switch_counts.append(var)

        # Create objective function - only need to change this now (will have to add more variables too)
        objective_terms = []
        for day in range(self.start_day, self.end_day + 1):
            for index, swimmer in enumerate(self.female_swimmers):
                objective_terms.append(swimmer.projected_points[day - 1] * (female_vars[day - self.start_day][index] + female_captain_vars[day - self.start_day][index]))
            for index, swimmer in enumerate(self.male_swimmers):
                objective_terms.append(swimmer.projected_points[day - 1] * (male_vars[day - self.start_day][index] + male_captain_vars[day - self.start_day][index]))

        self.solver.Maximize(sum(objective_terms))

        # Budget constraints
        for day in range(self.start_day, self.end_day + 1):
            budget_terms = []
            for index, swimmer in enumerate(self.female_swimmers):
                budget_terms.append(swimmer.cost * female_vars[day - self.start_day][index])
            for index, swimmer in enumerate(self.male_swimmers):
                budget_terms.append(swimmer.cost * male_vars[day - self.start_day][index])

            self.solver.Add(sum(budget_terms) <= BUDGET)

        # Number of females constraints
        for day in range(self.start_day, self.end_day + 1):
            self.solver.Add(sum(female_vars[day - self.start_day]) == ROSTER_SIZE // 2)

        # Number of males constraints
        for day in range(self.start_day, self.end_day + 1):
            self.solver.Add(sum(male_vars[day - self.start_day]) == ROSTER_SIZE // 2)

        # Captain constraints (can't be captain if not in lineup, exactly one captain per day)
        for day in range(self.start_day, self.end_day + 1):
            for swimmer_var, captain_var in zip(female_vars[day - self.start_day] + male_vars[day - self.start_day], female_captain_vars[day - self.start_day] + male_captain_vars[day - self.start_day], strict=True):
                self.solver.Add(captain_var <= swimmer_var)
            self.solver.Add(sum(male_captain_vars[day - self.start_day] + female_captain_vars[day - self.start_day]) == 1)

        # Total switches constraint (switches are double counted)
        self.solver.Add(sum(day_switch_counts) / 2 <= self.switches)

        # Day switch count constraints
        for day in range(self.start_day + 1, self.end_day + 1):
            self.solver.Add(day_switch_counts[day - self.start_day - 1] == sum(switch_vars[day - self.start_day - 1]))

        # Switch constraints
        for day in range(self.start_day + 1, self.end_day + 1):
            for index in range(self.num_females):
                x = female_vars[day - self.start_day][index]
                y = female_vars[day - self.start_day - 1][index]
                z = switch_vars[day - self.start_day - 1][index]
                self.solver.Add(z >= x - y)
                self.solver.Add(z >= y - x)
                self.solver.Add(z <= x + y)
                self.solver.Add(z <= 2 - (x + y))
            for index in range(self.num_males):
                x = male_vars[day - self.start_day][index]
                y = male_vars[day - self.start_day - 1][index]
                z = switch_vars[day - self.start_day - 1][index + self.num_females]
                self.solver.Add(z >= x - y)
                self.solver.Add(z >= y - x)
                self.solver.Add(z <= x + y)
                self.solver.Add(z <= 2 - (x + y))

        # Solve
        status = self.solver.Solve()

        # Check that solver worked
        if status != pywraplp.Solver.OPTIMAL:
            msg = f"Solver failed with status {status}. Exiting program."
            sys.exit(msg)

        # Get solution values

        self.solution_values = {}
        self.solution_values["swimmer_decision_vars"] = []
        for day_vars in [x + y for x, y in zip(female_vars, male_vars, strict=True)]:
            new_values = [var.solution_value() for var in day_vars]
            self.solution_values["swimmer_decision_vars"].append(new_values)

        self.solution_values["captain_decision_vars"] = []
        for day_vars in [x + y for x, y in zip(female_captain_vars, male_captain_vars, strict=True)]:
            new_values = [var.solution_value() for var in day_vars]
            self.solution_values["captain_decision_vars"].append(new_values)

        self.solution_values["switch_decision_vars"] = []
        for day_vars in switch_vars:
            new_values = [var.solution_value() for var in day_vars]
            self.solution_values["switch_decision_vars"].append(new_values)

        self.solution_values["day_switch_counts"] = [int(var.solution_value() / 2) for var in day_switch_counts]


    def _print_solution(self) -> None:
        """Print the optimal lineups for each day of the meet."""
        print()
        for day, day_solution_values in zip(range(self.start_day, self.end_day + 1), self.solution_values["swimmer_decision_vars"], strict=True):
            print(f"Day {day} lineup:")
            female_indices = list(filter(lambda x: day_solution_values[x], range(self.num_females)))
            female_swimmers = [self.female_swimmers[x] for x in female_indices]
            male_indices = list(filter(lambda x: day_solution_values[x], range(self.num_females, self.num_females + self.num_males)))
            male_swimmers = [self.male_swimmers[x - self.num_females] for x in male_indices]

            total_points = 0
            for swimmer in female_swimmers:
                if self.solution_values["captain_decision_vars"][day - self.start_day][self.female_swimmers.index(swimmer)]:
                    print(f"{swimmer.name} ({swimmer.projected_points[day - 1] * 2}) (---------- Captain ----------)")
                    total_points += swimmer.projected_points[day - 1] * 2
                else:
                    print(f"{swimmer.name} ({swimmer.projected_points[day - 1]})")
                    total_points += swimmer.projected_points[day - 1]
            for swimmer in male_swimmers:
                if self.solution_values["captain_decision_vars"][day - self.start_day][self.male_swimmers.index(swimmer) + self.num_females]:
                    print(f"{swimmer.name} ({swimmer.projected_points[day - 1] * 2}) (---------- Captain ----------)")
                    total_points += swimmer.projected_points[day - 1] * 2
                else:
                    print(f"{swimmer.name} ({swimmer.projected_points[day - 1]})")
                    total_points += swimmer.projected_points[day - 1]
            print(f"Day {day} total: {total_points}\n")

        print(f"Grand total: {int(self.solver.Objective().Value())} points")
        print(f"Switches used: {sum(self.solution_values['day_switch_counts'])} / {self.switches}\n")

    def _get_male_swimmers(self) -> list[Swimmer]:
        male_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Male"]
        self.num_males = len(male_swimmers)

        # Order by total projected points over the whole meet to make checking easier when switches is 0
        return sorted(male_swimmers, key=lambda x: sum(x.projected_points), reverse=True)


    def _get_female_swimmers(self) -> list[Swimmer]:
        female_swimmers = [swimmer for swimmer in self.all_swimmers if swimmer.sex == "Female"]
        self.num_females = len(female_swimmers)

        return sorted(female_swimmers, key=lambda x: sum(x.projected_points), reverse=True)
