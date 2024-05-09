"""This solves the simple pendulum swing up problem presented here:

http://hmc.csuohio.edu/resources/human-motion-seminar-jan-23-2014

A simple pendulum is controlled by a torque at its joint. The goal is to swing
the pendulum from its rest equilibrium to a target angle by minimizing the
energy used to do so in a minimal amount of time.

Solves the same problem as in ``pendulum_swing_up.py`` but with a variable
total duration.

"""

from collections import OrderedDict

import numpy as np
import sympy as sym
from opty.direct_collocation import Problem
from opty.utils import building_docs
import matplotlib.pyplot as plt
import matplotlib.animation as animation

target_angle = np.pi
num_nodes = 500
save_animation = False

# Symbolic equations of motion
m, g, d, t, h = sym.symbols('m, g, d, t, h')
theta, omega, T = sym.symbols('theta, omega, T', cls=sym.Function)

state_symbols = (theta(t), omega(t))
constant_symbols = (m, g, d)
specified_symbols = (T(t),)

eom = sym.Matrix([theta(t).diff() - omega(t),
                  m*d**2*omega(t).diff() + m*g*d*sym.sin(theta(t)) - T(t)])

# Specify the known system parameters.
par_map = OrderedDict()
par_map[m] = 1.0
par_map[g] = 9.81
par_map[d] = 1.0


# Specify the objective function and it's gradient.
def obj(free):
    """Minimize the sum of the squares of the control torque."""
    T = free[2 * num_nodes:]
    return free[-1]*np.sum(T**2)


def obj_grad(free):
    T = free[2 * num_nodes:]
    grad = np.zeros_like(free)
    grad[2 * num_nodes:] = 2.0 * free[-1] * free[2 * num_nodes:]
    grad[-1] = np.sum(T**2)
    return grad


# Specify the symbolic instance constraints, i.e. initial and end conditions
# using node numbers 1 to N.
instance_constraints = (theta(1*h),
                        theta(num_nodes*h) - target_angle,
                        omega(1*h),
                        omega(num_nodes*h))

# Create an optimization problem.
prob = Problem(obj, obj_grad, eom, state_symbols, num_nodes, h,
               known_parameter_map=par_map,
               instance_constraints=instance_constraints,
               time_symbol=t,
               bounds={T(t): (-2.0, 2.0), h: (0.0, 0.5)})

# Use a zero as an initial guess.
initial_guess = np.zeros(prob.num_free)

# Find the optimal solution.
solution, info = prob.solve(initial_guess)

# Make some plots
prob.plot_trajectories(solution)
prob.plot_constraint_violations(solution)
prob.plot_objective_value()

# Display animation
if not building_docs():
    interval_value = solution[-1]
    time = np.linspace(0.0, num_nodes*solution[-1], num=num_nodes)
    angle = solution[:num_nodes]

    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal', autoscale_on=False, xlim=(-2, 2),
                         ylim=(-2, 2))
    ax.grid()

    line, = ax.plot([], [], 'o-', lw=2)
    time_template = 'time = {:0.1f}s'
    time_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

    def init():
        line.set_data([], [])
        time_text.set_text('')
        return line, time_text

    def animate(i):
        x = [0, par_map[d] * np.sin(angle[i])]
        y = [0, -par_map[d] * np.cos(angle[i])]

        line.set_data(x, y)
        time_text.set_text(time_template.format(i*interval_value))
        return line, time_text

    ani = animation.FuncAnimation(fig, animate, np.arange(1, len(time)),
                                  interval=25, blit=True, init_func=init)

    if save_animation:
        ani.save('pendulum_swing_up_variable_duration.mp4', writer='ffmpeg',
                 fps=1 / interval_value)

plt.show()
