from ortools.linear_solver import pywraplp

class IntegerProgram:
    def __init__(self):
        # Mixed integer program solver
        self.solver = pywraplp.Solver.CreateSolver("SAT")