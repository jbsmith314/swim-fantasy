from ortools.linear_solver import pywraplp
from typing import List
from swimmer import Swimmer

class Solver:
    def __init__(self, swimmers):
        # Mixed integer program solver
        self.solver = pywraplp.Solver.CreateSolver("SAT")
        self.swimmers = swimmers
        self.male_swimmers = self.get_male_swimmers(swimmers)
        self.female_swimmers = self.get_female_swimmers(swimmers)
    

    def get_male_swimmers(self, swimmers: List[Swimmer]) -> List[Swimmer]:
        male_swimmers = []
        for swimmer in swimmers:
            if swimmer.sex == "Male":
                male_swimmers.append(swimmer)
        
        return male_swimmers
    

    def get_female_swimmers(self, swimmers: List[Swimmer]) -> List[Swimmer]:
        female_swimmers = []
        for swimmer in swimmers:
            if swimmer.sex == "Female":
                female_swimmers.append(swimmer)

        return female_swimmers
    

    def get_data(self, day: int):
        # female projected points from greatest to least
        # male projected points from greatest to least
        # female costs in same swimmer order as projected points
        # male costs in same swimmer order as projected points
        female_points = sorted(self.female_swimmers, key=lambda x: x.projected_points[day - 1])