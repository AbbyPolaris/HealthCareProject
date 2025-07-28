from pyomo.environ import *
from pyomo.opt import SolverFactory
from model import model
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pyomo.environ import value

data = DataPortal()
data.load(filename='parameters.dat')    

instance = model.create_instance(data=data) 
instance.write('model.lp', io_options={'symbolic_solver_labels': True})
solver = SolverFactory('glpk')
