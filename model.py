from pyomo.environ import *
infinity = float('inf')
model = AbstractModel(name='HealthCare Project')


#sets here
model.Nodes = Set()
model.Hospitals = Set()
model.BDCs = Set()
model.OpenBDCs = Set()

#model parameters here
model.M = 999999999
model.epsilon = 1e-9

model.g = Param(model.BDCs, within= NonNegativeReals)
model.p = Param(model.BDCs, within = NonNegativeIntegers)
model.D = Param()
model.h = Param(model.Hospitals, within= NonNegativeIntegers)
model.e = Param(model.Hospitals, within= NonNegativeReals)
model.b = Param(model.Hospitals, within= NonNegativeReals)
model.tn_n = Param(model.Nodes, model.Nodes,within= NonNegativeReals)
model.u = Param()
model.Q = Param()
model.s = Param()


#variables here
model.xn_n = Var(model.Nodes, Model.Nodes, within = Binary)
model.y = Var(model.BDCs, within= Binary)
model.zn_n = Var(model.Nodes, model.Nodes, within= NonNegativeIntegers)
model.U = Var(model.Hospitals, within= NonNegativeReals)
model.v = Var(model.Hospitals, within= NonNegativeReals)
model.GG = Var(model.Hospitals, within= NonNegativeReals)
model.EE = Var(model.Hospitals, within= NonNegativeReals)

#constraints here
