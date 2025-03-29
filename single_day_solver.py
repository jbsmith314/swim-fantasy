from ortools.linear_solver import pywraplp
from typing import List
from swimmer import Swimmer

ROSTER_SIZE = 8
BUDGET = 200

class SingleDaySolver:
    def __init__(self, swimmers: List[Swimmer], day: int):
        # Mixed integer program solver
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
    

    def get_data(self):
        # female projected points from greatest to least
        self.female_points = [x.projected_points[self.day - 1] for x in self.female_swimmers]
        # male projected points from greatest to least
        self.male_points = [x.projected_points[self.day - 1] for x in self.male_swimmers]

        # female costs in same swimmer order as projected points
        self.female_costs = [x.cost for x in self.female_swimmers]
        # male costs in same swimmer order as projected points
        self.male_costs = [x.cost for x in self.male_swimmers]
    

    def solve(self):
        self.solver = pywraplp.Solver.CreateSolver("SAT")
        self._create_variables()
        self._create_objective_function()
        self._create_constraints

        # Solve
        print(f"Solving with {self.solver.SolverVersion()}")
        status = self.solver.Solve()

        # Check that solver worked
        if status != pywraplp.Solver.OPTIMAL:
            raise Exception("No optimal solution found")

        optimal_lineup, captain = self._get_optimal_lineup()
        print("The optimal lineup is:")
        self._print_lineup(optimal_lineup, captain)
        print(f"With a total score of: {self.solver.Objective().Value()}")


    def _get_optimal_lineup(self):
        # Make female_swimmers_list to be executed later"
        female_swimmers_list = ""
        for i in range(self.num_females):
            female_swimmers_list += f"self.x{i + 1}, "
        female_swimmers_list = f"[{female_swimmers_list.rstrip(", ")}]"

        # Make male_swimmers_list to be executed later"
        male_swimmers_list = ""
        for i in range(self.num_males):
            male_swimmers_list += f"self.y{i + 1}, "
        male_swimmers_list = f"[{male_swimmers_list.rstrip(", ")}]"

        # Make solution_values_list to be executed later"
        solution_values_list = ""
        for i in range(self.num_females):
            solution_values_list += f"self.x{i + 1}.solution_value(), "
        for i in range(self.num_males):
            solution_values_list += f"self.y{i + 1}.solution_value(), "
        solution_values_list = f"[{solution_values_list.rstrip(", ")}]"

        female_swimmers = []
        exec("female_swimmers = " + female_swimmers_list)
        male_swimmers = []
        exec("male_swimmers = " + male_swimmers_list)
        solution_values = []
        exec("solution_values = " + solution_values_list)

        indices = list(filter(lambda x: solution_values[x], range(self.num_females)))
        lineup_female = list(map(lambda x: self.female_swimmers[x], indices))

        indices = list(filter(lambda x: solution_values[x], range(self.num_females, self.num_females + self.num_males)))
        lineup_male = list(map(lambda x: self.female_swimmers[x], indices))

        lineup = lineup_female + lineup_male
        captain = max(lineup, key=lambda x: x.projected_points[self.day - 1])

        return lineup, captain


    def _create_variables(self):
        # declare decision variables for female swimmers
        for index in range(self.num_females):
            new_constraint = f"x{index + 1} = self.solver.IntVar(0, 1, 'x{index + 1}')"
            exec(new_constraint)

        # declare decision variables for male swimmers
        for index in range(self.num_males):
            new_constraint = f"y{index + 1} = self.solver.IntVar(0, 1, 'y{index + 1}')"
            exec(new_constraint)
    

    def _create_objective_function(self):
        print(len(self.solver.variables()))

        # create and declare objective function
        objective_function = ""
        for index in range(self.num_females):
            num = self.female_points[index]
            objective_function += f"{num}*x{index + 1} + "
        for index in range(self.num_males):
            num = self.male_points[index]
            objective_function += f"{num}*y{index + 1} + "
        objective_function = f"self.solver.Maximize({objective_function.rstrip("+ ")})"
        exec(objective_function)
    

    def _create_constraints(self):
        # budget constraint
        budget_constraint = ""
        for index in range(self.num_females):
            num = self.female_costs[index]
            budget_constraint += f"{num}*x{index + 1} + "
        for index in range(self.num_males):
            num = self.male_costs[index]
            budget_constraint += f"{num}*y{index + 1} + "
        budget_constraint = f"self.solver.Add({budget_constraint.rstrip("+ ")} <= {BUDGET})"
        exec(budget_constraint)

        # number of females constraint
        num_females_constraint = "self.solver.Add("
        for index in range(self.num_females):
            num_females_constraint += f"x{index + 1} + "
        exec(num_females_constraint.rstrip("+ ") + f" <= {ROSTER_SIZE / 2})")

        # number of males constraint
        num_males_constraint = "self.solver.Add("
        for index in range(self.num_males):
            num_males_constraint += f"y{index + 1} + "
        exec(num_males_constraint.rstrip("+ ") + f" <= {ROSTER_SIZE / 2})")
    

    def _print_lineup(self, lineup, captain):
        for swimmer in lineup:
            print(f"{swimmer.name}", end="")
            if swimmer is captain:
                print(" (Captain)")
            print()
    

    def _get_male_swimmers(self, swimmers: List[Swimmer]) -> List[Swimmer]:
        male_swimmers = []
        for swimmer in swimmers:
            if swimmer.sex == "Male":
                male_swimmers.append(swimmer)
        
        return sorted(male_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)
    

    def _get_female_swimmers(self, swimmers: List[Swimmer]) -> List[Swimmer]:
        female_swimmers = []
        for swimmer in swimmers:
            if swimmer.sex == "Female":
                female_swimmers.append(swimmer)

        return sorted(female_swimmers, key=lambda x: x.projected_points[self.day - 1], reverse=True)