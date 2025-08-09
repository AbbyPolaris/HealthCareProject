from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from model import model  # your Pyomo model file

# ---------------- Parameters ----------------
DATA_FILE = '/home/abby/HCProj/parameters.dat'
SOLVER_NAME = 'glpk'
STEPS_NUMBER = 10  # number of epsilon steps


# -------------- Load Data & Initialize --------------
data = DataPortal()
data.load(filename=DATA_FILE)
base_model = model.create_instance(data=data)
solver = SolverFactory(SOLVER_NAME)


def activate_objective(m, objective_name):
    """
    Deactivate all objectives except the one specified.
    """
    for obj in ['obj1', 'obj2']:
        if hasattr(m, obj):
            getattr(m, obj).deactivate()
    getattr(m, objective_name).activate()


def solve_model(m, tee=False):
    """
    Solve the Pyomo model instance.
    """
    result = solver.solve(m, tee=tee)
    termination = getattr(result.solver, 'termination_condition', None)
    status = getattr(result.solver, 'status', None)
    return result, termination, status


def compute_objective_extremes(base):
    """
    Compute extreme solutions by minimizing each objective separately.
    Returns tuple: ((obj1_min, obj2_at_obj1_min), (obj1_at_obj2_min, obj2_min))
    """
    # Minimize obj1
    m1 = base.clone()
    activate_objective(m1, 'obj1')
    _, tc1, st1 = solve_model(m1)
    obj1_min = value(m1.obj1.expr)
    obj2_at_obj1_min = value(m1.obj2.expr)
    print(f"Min obj1: {obj1_min:.4f}, Obj2 at obj1 min: {obj2_at_obj1_min:.4f} (tc={tc1}, status={st1})")

    # Minimize obj2
    m2 = base.clone()
    activate_objective(m2, 'obj2')
    _, tc2, st2 = solve_model(m2)
    obj2_min = value(m2.obj2.expr)
    obj1_at_obj2_min = value(m2.obj1.expr)
    print(f"Min obj2: {obj2_min:.4f}, Obj1 at obj2 min: {obj1_at_obj2_min:.4f} (tc={tc2}, status={st2})")

    return (obj1_min, obj2_at_obj1_min), (obj1_at_obj2_min, obj2_min)

def epsilon_constraint_method(base, epsilon_values, constrained_obj_name, main_obj_name):
    """
    Run epsilon-constraint method:
    - Optimize main_obj_name
    - Constrain constrained_obj_name <= epsilon (if minimizing) or >= epsilon (if maximizing)
    """
    results = []

    print(f"{'Epsilon':>10} | {'Obj1':>12} | {'Obj2':>12} | {'Slack':>10} | {'Termination':>12} | {'Status':>10}")
    print("-" * 75)

    for eps in epsilon_values:
        m = base.clone()
        activate_objective(m, main_obj_name)
        cobj = getattr(m, constrained_obj_name)

        # Create constraint expression based on sense
        if cobj.sense == maximize:
            constraint_expr = cobj.expr >= eps
        else:
            constraint_expr = cobj.expr <= eps

        constraint_name = f"{constrained_obj_name}_epsilon_constraint"
        m.add_component(constraint_name, Constraint(expr=constraint_expr))

        result, termination, status = solve_model(m)

        obj1_val = value(m.obj1.expr)
        obj2_val = value(m.obj2.expr)
        constrained_val = value(cobj.expr)

        slack = (constrained_val - eps) if cobj.sense == maximize else (eps - constrained_val)

        print(f"{eps:10.4f} | {obj1_val:12.4f} | {obj2_val:12.4f} | {slack:10.4f} | {str(termination):>12} | {str(status):>10}")

        results.append({
            'epsilon': eps,
            'obj1': obj1_val,
            'obj2': obj2_val,
            'constrained_value': constrained_val,
            'slack': slack,
            'termination': str(termination),
            'status': str(status),
            'constrained_obj_sense': 'max' if cobj.sense == maximize else 'min'
        })

    return pd.DataFrame(results)

def plot_obj_vs_epsilon(df, main_obj_name, filename):
    """
    Plot the main objective value against epsilon values,
    then save the plot to the specified filename.
    """
    plt.figure(figsize=(7, 5))
    plt.plot(df['epsilon'], df[main_obj_name], marker='o', linestyle='-', color='tab:blue')
    plt.xlabel('Epsilon (constraint bound)')
    plt.ylabel(f'{main_obj_name} value')
    plt.title(f'{main_obj_name} vs. Epsilon')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Plot saved as {filename}")
    plt.show()

def plot_pareto_front(df, filename='pareto_front.png'):
    """
    Plot the Pareto front: obj1 vs obj2 scatter plot, save to filename.
    """
    plt.figure(figsize=(7,6))
    plt.scatter(df['obj1'], df['obj2'], s=80, c='green', alpha=0.7, label='Pareto Points')
    
    # Optionally connect points to visualize the frontier shape
    sorted_df = df.sort_values(by='obj1')  # sort by obj1 for a nicer line
    plt.plot(sorted_df['obj1'], sorted_df['obj2'], linestyle='--', color='orange', label='Pareto Frontier')

    plt.xlabel('Objective 1')
    plt.ylabel('Objective 2')
    plt.title('Pareto Front')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Pareto plot saved as {filename}")
    plt.show()

def main():
    # Compute extreme points of the objectives
    (o1_min, o2_at_o1_min), (o1_at_o2_min, o2_min) = compute_objective_extremes(base_model)

    # Define epsilon arrays for constrained objectives
    obj2_epsilons = np.linspace(min(o2_min, o2_at_o1_min), max(o2_min, o2_at_o1_min), STEPS_NUMBER)
    obj1_epsilons = np.linspace(min(o1_min, o1_at_o2_min), max(o1_min, o1_at_o2_min), STEPS_NUMBER)

    # Run epsilon-constraint: obj2 constrained, obj1 minimized
    df1 = epsilon_constraint_method(base_model, obj2_epsilons, constrained_obj_name='obj2', main_obj_name='obj1')

    # Run epsilon-constraint: obj1 constrained, obj2 minimized
    df2 = epsilon_constraint_method(base_model, obj1_epsilons, constrained_obj_name='obj1', main_obj_name='obj2')

    # Combine results & remove duplicates (optional)
    df_all = pd.concat([df1, df2], ignore_index=True)
    df_all[['obj1', 'obj2']] = df_all[['obj1', 'obj2']].round(8)
    df_unique = df_all.drop_duplicates(subset=['obj1', 'obj2']).reset_index(drop=True)

    print(f"\nUnique Pareto solutions found: {len(df_unique)}")
    print(df_unique[['obj1', 'obj2', 'epsilon', 'slack', 'termination', 'constrained_obj_sense']])

    # Plot and save obj1 vs epsilon
    plot_obj_vs_epsilon(df1, main_obj_name='obj1', filename='obj1_vs_epsilon.png')

    # Plot and save obj2 vs epsilon
    plot_obj_vs_epsilon(df2, main_obj_name='obj2', filename='obj2_vs_epsilon.png')
        
    plot_pareto_front(df_unique, filename='pareto_front.png')

if __name__ == "__main__":
    main()
