# import solver for linear program
from ortools.linear_solver import pywraplp

INPUT_FILE = "2023 LP Day 2.txt"
MAX_COST = 100
NUM_LINEUPS = 10
ROSTER_SIZE = 8
BUDGET = 200

# get mip solver
solver = pywraplp.Solver.CreateSolver("SAT")

# get input file name from user
# file should contain one number per line, in the order of:
# female projected points from greatest to least
# male projected points from greatest to least
# female costs in same swimmer order as projected points
# male costs in same swimmer order as projected points
imported_values = open(INPUT_FILE)
data = []
for value in imported_values:
    data.append(int(value.strip()))

# projected points for females and males
female_projected_points = [data[0]]
index = 1
while data[index] <= data[index - 1]:
    female_projected_points.append(data[index])
    index += 1

num_females = len(female_projected_points)

male_projected_points = []
while data[index] > MAX_COST:
    male_projected_points.append(data[index])
    index += 1

num_males = len(male_projected_points)

# costs for females and males
female_costs = []
for i in range(num_females + num_males, 2 * num_females + num_males):
    female_costs.append(data[i])

male_costs = []
for i in range(2 * num_females + num_males, 2 * num_females + 2 * num_males):
    male_costs.append(data[i])

# declare decision variables for female swimmers
for index in range(num_females):
    new_constraint = f"x{index + 1} = solver.IntVar(0, 1, 'x{index + 1}')"
    exec(new_constraint)

# declare decision variables for male swimmers
for index in range(num_males):
    new_constraint = f"y{index + 1} = solver.IntVar(0, 1, 'y{index + 1}')"
    exec(new_constraint)

# create and declare objective function
object_function = ""
for index in range(num_females):
    num = female_projected_points[index]
    object_function += f"{num}*x{index + 1} + "
for index in range(num_males):
    num = male_projected_points[index]
    object_function += f"{num}*y{index + 1} + "
object_function = f"solver.Maximize({object_function.rstrip("+ ")})"
exec(object_function)

# budget constraint
budget_constraint = ""
for index in range(num_females):
    num = female_costs[index]
    budget_constraint += f"{num}*x{index + 1} + "
for index in range(num_males):
    num = male_costs[index]
    budget_constraint += f"{num}*y{index + 1} + "
budget_constraint = f"solver.Add({budget_constraint.rstrip("+ ")} <= {BUDGET})"
exec(budget_constraint)

# number of females constraint
num_females_constraint = "solver.Add("
for index in range(num_females):
    num_females_constraint += f"x{index + 1} + "
exec(num_females_constraint.rstrip("+ ") + f" <= {ROSTER_SIZE / 2})")

# number of males constraint
num_males_constraint = "solver.Add("
for index in range(num_males):
    num_males_constraint += f"y{index + 1} + "
exec(num_males_constraint.rstrip("+ ") + f" <= {ROSTER_SIZE / 2})")

# print("Number of constraints =", solver.NumConstraints())

# Solve
# print(f"Solving with {solver.SolverVersion()}")
status = solver.Solve()

# Check that solver worked
if status != pywraplp.Solver.OPTIMAL:
    print("The problem does not have an optimal solution.")

# Adjusted order
female_real_points = [948, 941, 955, 941, 942, 916, 895, 949, 928, 905, 904, 920, 966, 975, 957, 907, 896, 906, 880, 937, 940, 956, 876, 919, 883, 901, 920, 910, 823, 874, 910, 829, 935, 911, 894, 885, 909, 894, 905, 887, 895, 872, 859, 887, 887, 878]
male_real_points = [1915, 946, 912, 920, 954, 919, 958, 912, 925, 927, 929, 915, 930, 890, 932, 920, 903, 878, 886, 909, 907, 909, 890, 906, 883, 899, 909, 902, 892, 861, 892, 909, 876, 892, 874, 909, 875, 914, 886, 858, 858, 869, 893, 873, 906, 872, 876]

# Make female_swimmers_list to be executed later"
female_swimmers_list = ""
for i in range(num_females):
    female_swimmers_list += f"x{i + 1}, "
female_swimmers_list = f"[{female_swimmers_list.rstrip(", ")}]"

# Make male_swimmers_list to be executed later"
male_swimmers_list = ""
for i in range(num_males):
    male_swimmers_list += f"y{i + 1}, "
male_swimmers_list = f"[{male_swimmers_list.rstrip(", ")}]"

# Make solution_values_list to be executed later"
solution_values_list = ""
for i in range(num_females):
    solution_values_list += f"x{i + 1}.solution_value(), "
for i in range(num_males):
    solution_values_list += f"y{i + 1}.solution_value(), "
solution_values_list = f"[{solution_values_list.rstrip(", ")}]"

# Get the NUM_LINEUPS top lineups
real_place = 1
prev_points = 0
max_score = 0
for i in range(NUM_LINEUPS):
    # Solve
    results = solver.Solve()

    # Get place of solution
    if solver.Objective().Value() != prev_points:
        real_place = i + 1
    
    # Get value of optimal solution
    prev_points = solver.Objective().Value()

    female_swimmers = []
    exec("female_swimmers = " + female_swimmers_list)
    male_swimmers = []
    exec("male_swimmers = " + male_swimmers_list)
    solution_values = []
    exec("solution_values = " + solution_values_list)

    lineup = []
    lineup_index = 0
    most_points = 0
    most_real_points = 0
    real_score = 0

    # Add female swimmers to lineup, add to real_score, and adjust most_points if needed
    for index, swimmer in enumerate(female_swimmers):
        if solution_values[index] > 0:
            lineup.append(swimmer)
            real_score += female_real_points[index]
            if female_real_points[index] > most_real_points:
                most_real_points = female_projected_points[index]
            if female_projected_points[index] > most_points:
                most_points = female_projected_points[index]
    
    # Add male swimmers to lineup, add to real_score, and adjust most_points if needed
    for index, swimmer in enumerate(male_swimmers):
        if solution_values[index + len(female_swimmers)] > 0:
            lineup.append(swimmer)
            real_score += male_real_points[index]
            if male_real_points[index] > most_real_points:
                most_real_points = male_projected_points[index]
            if male_projected_points[index] > most_points:
                most_points = male_projected_points[index]
    
    # Make optimal solution not allowed anymore
    new_constraint = "solver.Add("
    for index in range(len(lineup)):
        new_constraint += str(lineup[index]) + " + "
    new_constraint = new_constraint.rstrip("+ ") + f" <= {ROSTER_SIZE - 1}) # ({int(solver.Objective().Value() + most_points)})"
    print(f"({real_score + most_real_points}) {real_place}. {new_constraint}")
    exec(new_constraint)

    # Keep track of max real score
    if real_score + most_real_points > max_score:
        max_score = real_score + most_real_points

print(max_score)