# import solver for linear program
from ortools.linear_solver import pywraplp

# get mip solver
solver = pywraplp.Solver.CreateSolver("SAT")

# get input file name from user
# file should contain one number per line, in the order of:
# female projected points from greatest to least
# male projected points from greatest to least
# female costs in same swimmer order as projected points
# male costs in same swimmer order as projected points
while True:
    try:
        imported_values = open(input("Enter the file name to import: "))
        data = []
        for value in imported_values:
            data.append(int(value.strip()))
        break

    except FileNotFoundError:
        print("\nInvalid file name")
        print("Example input: example.txt")
        print("Also, the file must be in the same folder as this file\n")

# projected points for females and males
female_projected_points = [data[0]]
index = 1
while data[index] <= data[index - 1]:
    female_projected_points.append(data[index])
    index += 1

num_females = len(female_projected_points)

male_projected_points = []
while data[index] > 100:
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
new_constraint = "solver.Maximize("
for index in range(num_females):
    num = female_projected_points[index]
    new_constraint += f"{num}*x{index + 1} + "
for index in range(num_males - 1):
    num = male_projected_points[index]
    new_constraint += f"{num}*y{index + 1} + "
num = male_projected_points[num_males - 1]
new_constraint += f"{num}*y{num_males})"
exec(new_constraint)

# budget constraint
new_constraint = "solver.Add("
for index in range(num_females):
    num = female_costs[index]
    new_constraint += f"{num}*x{index + 1} + "
for index in range(num_males - 1):
    num = male_costs[index]
    new_constraint += f"{num}*y{index + 1} + "
num = male_costs[num_males - 1]
new_constraint += f"{num}*y{num_males} <= 200)"
exec(new_constraint)

# number of females constraint
new_constraint = "solver.Add("
for index in range(num_females - 1):
    new_constraint += f"x{index + 1} + "
new_constraint += f"x{num_females} <= 4)"
exec(new_constraint)

# number of males constraint
new_constraint = "solver.Add("
for index in range(num_males - 1):
    new_constraint += f"y{index + 1} + "
new_constraint += f"y{num_males} <= 4)"
exec(new_constraint)

print("Number of constraints =", solver.NumConstraints())

# solve
print(f"Solving with {solver.SolverVersion()}")
status = solver.Solve()

if status != pywraplp.Solver.OPTIMAL:
    print("The problem does not have an optimal solution.")

# adjusted order
female_real_points = [948, 941, 955, 941, 942, 916, 895, 949, 928, 905, 904, 920, 966, 975, 957, 907, 896, 906, 880, 937, 940, 956, 876, 919, 883, 901, 920, 910, 823, 874, 910, 829, 935, 911, 894, 885, 909, 894, 905, 887, 895, 872, 859, 887, 887, 878]
male_real_points = [1915, 946, 912, 920, 954, 919, 958, 912, 925, 927, 929, 915, 930, 890, 932, 920, 903, 878, 886, 909, 907, 909, 890, 906, 883, 899, 909, 902, 892, 861, 892, 909, 876, 892, 874, 909, 875, 914, 886, 858, 858, 869, 893, 873, 906, 872, 876]

# get best lineups
choose_num_lineups = False
if choose_num_lineups:
    num_lineups = int(input("Enter how many lineups you want: "))
else:
    num_lineups = 10
place = 0
real_place = 1
prev_points = 0
max_score = 0
for i in range(num_lineups):
    place += 1
    # solve
    results = solver.Solve()
    if solver.Objective().Value() != prev_points:
        real_place = place
    prev_points = solver.Objective().Value()
    female_swimmers = [x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32, x33, x34]
    male_swimmers = [y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14, y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32, y33, y34, y35, y36, y37, y38, y39, y40, y41, y42]
    solution_values = [x1.solution_value(), x2.solution_value(), x3.solution_value(), x4.solution_value(), x5.solution_value(), x6.solution_value(), x7.solution_value(), x8.solution_value(), x9.solution_value(), x10.solution_value(), x11.solution_value(), x12.solution_value(), x13.solution_value(), x14.solution_value(), x15.solution_value(), x16.solution_value(), x17.solution_value(), x18.solution_value(), x19.solution_value(), x20.solution_value(), x21.solution_value(), x22.solution_value(), x23.solution_value(), x24.solution_value(), x25.solution_value(), x26.solution_value(), x27.solution_value(), x28.solution_value(), x29.solution_value(), x30.solution_value(), x31.solution_value(), x32.solution_value(), x33.solution_value(), x34.solution_value(), y1.solution_value(), y2.solution_value(), y3.solution_value(), y4.solution_value(), y5.solution_value(), y6.solution_value(), y7.solution_value(), y8.solution_value(), y9.solution_value(), y10.solution_value(), y11.solution_value(), y12.solution_value(), y13.solution_value(), y14.solution_value(), y15.solution_value(), y16.solution_value(), y17.solution_value(), y18.solution_value(), y19.solution_value(), y20.solution_value(), y21.solution_value(), y22.solution_value(), y23.solution_value(), y24.solution_value(), y25.solution_value(), y26.solution_value(), y27.solution_value(), y28.solution_value(), y29.solution_value(), y30.solution_value(), y31.solution_value(), y32.solution_value(), y33.solution_value(), y34.solution_value(), y35.solution_value(), y36.solution_value(), y37.solution_value(), y38.solution_value(), y39.solution_value(), y40.solution_value(), y41.solution_value(), y42.solution_value()]
    lineup = []
    lineup_index = 0
    most_points = 0
    real_most_points = 0
    real_score = 0
    for index, swimmer in enumerate(female_swimmers):
        if solution_values[index] > 0:
            lineup.append(swimmer)
            real_score += female_real_points[index]
            if female_real_points[index] > real_most_points:
                real_most_points = female_projected_points[index]
            if female_projected_points[index] > most_points:
                most_points = female_projected_points[index]
    for index, swimmer in enumerate(male_swimmers):
        if solution_values[index + len(female_swimmers)] > 0:
            lineup.append(swimmer)
            real_score += male_real_points[index]
            if male_real_points[index] > real_most_points:
                real_most_points = male_projected_points[index]
            if male_projected_points[index] > most_points:
                most_points = male_projected_points[index]
    new_constraint = "solver.Add("
    for index in range(len(lineup) - 1):
        new_constraint += str(lineup[index])
        new_constraint += " + "
    new_constraint += f"{lineup[7]} <= 7) # ({int(solver.Objective().Value() + most_points)})"
    print(f"({real_score + real_most_points}) {real_place}. {new_constraint}")
    exec(new_constraint)
    if real_score + real_most_points > max_score:
        max_score = real_score + real_most_points
print(max_score)