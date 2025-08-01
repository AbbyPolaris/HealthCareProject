from pyomo.environ import *

infinity = float('inf')
model = AbstractModel(name='HealthCare Project')

# sets here
model.Nodes = Set()
model.Hospitals = Set()
model.BDCs = Set()
model.OpenBDCs = Set()

# model parameters here
model.M = 999999999
model.epsilon = 1e-9

model.g = Param(model.BDCs, within=NonNegativeReals)
model.p = Param(model.BDCs, within=NonNegativeIntegers)
model.D = Param()
model.h = Param(model.Hospitals, within=NonNegativeIntegers)
model.e = Param(model.Hospitals, within=NonNegativeReals)
model.b = Param(model.Hospitals, within=NonNegativeReals)
model.tn_n = Param(model.Nodes, model.Nodes, within=NonNegativeReals)
model.u = Param()
model.Q = Param()
model.s = Param()

# variables here
model.xn_n = Var(model.Nodes, model.Nodes, within=Binary)
model.y = Var(model.BDCs, within=Binary)
model.zn_n = Var(model.Nodes, model.Nodes, within=NonNegativeIntegers)
model.U = Var(model.Hospitals, within=NonNegativeReals)
model.v = Var(model.Hospitals, within=NonNegativeReals)
model.GG = Var(model.Hospitals, within=NonNegativeReals)
model.EE = Var(model.Hospitals, within=NonNegativeReals)


# constraints here, we write m for model
# in constraint to avoid unnecessary misunderstandings or conflicts
def hospital_visited_once_rule(m, j):  # each hospital mus be visited exactly once.
    return sum(m.xn_n[d, j] for d in m.BDCs) + \
        sum(m.xn_n[i, j] for i in m.Hospitals if i != j) == 1


model.hospital_visited_once = Constraint(model.Hospitals, hospital_visited_once_rule)


def subtour_elimination1_rule(m, i, j):
    if i != j:
        return m.U[i] - m.U[j] + m.s * m.xn_n[i, j] + (m.s - 2) * m.xn_n[j, i] <= m.s - 1
    else:
        return Constraint.Skip  # Skip when i == j


model.subtour_elimination1 = Constraint(model.Hospitals, model.Hospitals, rule=subtour_elimination1_rule)


def subtour_elimination2_rule(m, i):

    return sum(m.xn_n[i, j] for j in m.Hospitals if j != i) <= m.U[i] * len(m.Hospitals)


model.subtour_elimination2 = Constraint(model.Hospitals, rule=subtour_elimination2_rule)


def meet_blood_needs_hospitals_rule(m, d):
    return sum(m.zn_n[d, i] for i in m.Hospitals) == sum(m.h[i] * m.xn_n[d, i] for i in m.Hospitals)


model.meet_blood_needs = Constraint(model.BDCs, rule=meet_blood_needs_hospitals_rule)


def BDC_blood_capacity_rule(m, d):
    return sum(m.zn_n[d, i] for i in m.Hospitals) <= m.p[d] * m.y[d]


model.BDC_blood_capacity = Constraint(model.BDCs, rule=BDC_blood_capacity_rule)


def meet_hospitals_demand_rule(m, i):
    return sum(m.zn_n[d, i] for d in m.BDCs) + sum(m.zn_n[j, i] for j in m.Hospitals if j != i) >= m.h[i]


model.meet_hospital_demand = Constraint(model.Hospitals, rule=meet_hospitals_demand_rule)


def routing1_rule(m, i, j): # This is constraint 9 of the mathematical model.
    if i != j:
        return m.zn_n[i, j] <= m.h[j] * m.xn_n[i, j]
    else:
        return Constraint.Skip


model.routing1 = Constraint(model.Hospitals, model.Hospitals, rule= routing1_rule)


def routing2_rule(m, d, i): # This is constraint 10 of the mathematical model.
    return m.zn_n[d, i] <= m.h[i] * m.xn_n[d, i]


model.routing2 = Constraint(model.BDCs, model.Hospitals, rule=routing2_rule)


def blood_relationship_BDCs_hospitals_rule(m, i):
    return sum(m.zn_n[d, i] for d in m.BDCs) >= sum(m.zn_n[i, j] for j in m.Hospitals if j != i )


model.blood_relationship_BDCs_hospitals = Constraint(model.Hospitals, rule=blood_relationship_BDCs_hospitals_rule)


def open_stationary_BDCs_rule(m, o):
    return m.y[o] == 1


model.open_stationary_BDCs = Constraint(model.OpenBDCs, rule=open_stationary_BDCs_rule)


def arrival_time1_rule(m, i):
    return m.v[i] == sum(m.tn_n[d, i] * m.xn_n[d, i] for d in m.BDCs)


model.arrival_time1 = Constraint(model.Hospitals, rule=arrival_time1_rule)


def arrival_time2_rule(m, j):
    return m.v[j] <= sum(m.tn_n[i, j] * m.xn_n[i, j] + m.v[i] for i in m.Hospitals if i!=j)


model.arrival_time2 = Constraint(model.Hospitals, rule=arrival_time2_rule)


def tardiness_rule(m, i):
    return m.GG[i] >= m.v[i] - m.b[i]


model.tardiness = Constraint(model.Hospitals, rule=tardiness_rule)


def earliness_rule(m, i):
    return m.EE[i] >= m.e[i] - m.v[i]


model.earliness = Constraint(model.Hospitals, rule=earliness_rule)


def objective_function_cost_rule(m):
    return sum(m.g[d] * m.y[d] for d in m.BDCS) + sum(m.u * m.tn_n[i, j] * (m.zn_n[i, j] / m.Q) for i in m.Nodes for j in m.Nodes )


def objective_function_punctuality_rule(m):
    return sum(m.EE[i] for i in m.Hospitals) + sum(m.GG for i in m.Hospitals)


model.obj1 = Objective(rule=objective_function_cost_rule, sense=minimize)
model.obj2 = Objective(rule=objective_function_punctuality_rule, sense=minimize)





