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
        self.solution_values = []
    

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
        self._get_solution()

        optimal_lineup, captain = self._get_optimal_lineup()
        print("The optimal lineup is:")
        self._print_lineup(optimal_lineup, captain)
        print(f"With a total score of: {int(self.solver.Objective().Value() + captain.projected_points[self.day - 1])}")


    def _get_optimal_lineup(self):
        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females)))
        lineup_female = list(map(lambda x: self.female_swimmers[x], indices))

        indices = list(filter(lambda x: self.solution_values[x], range(self.num_females, self.num_females + self.num_males)))
        lineup_male = list(map(lambda x: self.male_swimmers[x - self.num_females], indices))

        lineup = lineup_female + lineup_male
        captain = max(lineup, key=lambda x: x.projected_points[self.day - 1])

        return lineup, captain


    def _get_solution(self):
        # Declare decision variables for female swimmers
        for index in range(self.num_females):
            new_constraint = f"x{index + 1} = self.solver.IntVar(0, 1, 'x{index + 1}')"
            exec(new_constraint)

        # Declare decision variables for male swimmers
        for index in range(self.num_males):
            new_constraint = f"y{index + 1} = self.solver.IntVar(0, 1, 'y{index + 1}')"
            exec(new_constraint)

        # Create and declare objective function
        objective_function = ""
        for index, swimmer in enumerate(self.female_swimmers):
            objective_function += f"{swimmer.projected_points[self.day - 1]}*x{index + 1} + "
        for index, swimmer in enumerate(self.male_swimmers):
            objective_function += f"{swimmer.projected_points[self.day - 1]}*y{index + 1} + "
        objective_function = f"self.solver.Maximize({objective_function.rstrip("+ ")})"
        exec(objective_function)
    
        # Budget constraint
        budget_constraint = ""
        for index, swimmer in enumerate(self.female_swimmers):
            budget_constraint += f"{swimmer.cost}*x{index + 1} + "
        for index, swimmer in enumerate(self.male_swimmers):
            budget_constraint += f"{swimmer.cost}*y{index + 1} + "
        budget_constraint = f"self.solver.Add({budget_constraint.rstrip("+ ")} <= {BUDGET})"
        exec(budget_constraint)

        # Number of females constraint
        num_females_constraint = "self.solver.Add("
        for index in range(self.num_females):
            num_females_constraint += f"x{index + 1} + "
        num_females_constraint = f"{num_females_constraint.rstrip("+ ")} <= {ROSTER_SIZE / 2})"
        exec(num_females_constraint)

        # Number of males constraint
        num_males_constraint = "self.solver.Add("
        for index in range(self.num_males):
            num_males_constraint += f"y{index + 1} + "
        num_males_constraint = f"{num_males_constraint.rstrip("+ ")} <= {ROSTER_SIZE / 2})"
        exec(num_males_constraint)

        # Solve
        print(f"Solving with {self.solver.SolverVersion()}")
        status = self.solver.Solve()

        # Check that solver worked
        if status != pywraplp.Solver.OPTIMAL:
            raise Exception("No optimal solution found")

        # Make solution_values_list"
        solution_values_list = ""
        for i in range(self.num_females):
            solution_values_list += f"x{i + 1}.solution_value(), "
        for i in range(self.num_males):
            solution_values_list += f"y{i + 1}.solution_value(), "
        solution_values_list = f"[{solution_values_list.rstrip(", ")}]"

        exec(f"self.solution_values = {solution_values_list}")
    

    def _print_lineup(self, lineup, captain):
        for swimmer in lineup:
            print(f"{swimmer.name}", end="")
            if swimmer is captain:
                print(f" (Captain) ({int(swimmer.projected_points[self.day - 1] * 2)})", end="")
            else:
                print(f" ({int(swimmer.projected_points[self.day - 1])})", end="")
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