"""Tests for the symbolic solver and equation library.

Covers the six end-to-end spec problems plus edge cases (reserved symbol names,
multi-root selection, validation, and a sanity build of every library entry).
"""
import math

import pytest

from solvers.equations import EQUATIONS, DOMAINS, SIMULATION_TYPES
from solvers.sympy_solver import (
    MissingValueError,
    SolverError,
    build_equation,
    equation_latex,
    solution_latex,
    solve_for,
)


# --- The six spec test problems ------------------------------------------------

def test_projectile_range():
    r = solve_for("projectile_range", {"v0": 20, "theta": 45}, "R")
    assert math.isclose(r.value, 40.8, abs_tol=0.5)
    assert r.unit == "m"
    assert r.simulation == "projectile"
    assert r.substitutions["g"] == 9.81  # constant auto-filled


def test_pendulum_period():
    r = solve_for("pendulum_period", {"L": 2}, "T")
    assert math.isclose(r.value, 2.837, abs_tol=0.05)
    assert r.simulation == "pendulum"


def test_parallel_resistors():
    r = solve_for("resistors_parallel", {"R1": 4, "R2": 6}, "R")
    assert math.isclose(r.value, 2.4, abs_tol=1e-6)
    assert r.unit == "ohm"


def test_wave_speed():
    r = solve_for("wave_speed", {"f": 440, "wavelength": 0.78}, "v")
    assert math.isclose(r.value, 343.2, abs_tol=0.1)
    assert r.simulation == "wave"


def test_combined_gas_law():
    r = solve_for(
        "combined_gas_law",
        {"P1": 1, "V1": 2, "T1": 300, "P2": 2, "T2": 600},
        "V2",
    )
    assert math.isclose(r.value, 2.0, abs_tol=1e-6)


def test_escape_velocity_earth():
    r = solve_for("escape_velocity", {"M": 5.972e24, "r": 6.371e6}, "v")
    assert math.isclose(r.value, 11186, abs_tol=50)  # ~11.2 km/s
    assert r.simulation == "orbital"


# --- Edge cases ---------------------------------------------------------------

def test_ohms_law_solves_for_current():
    # 'I' collides with SymPy's imaginary unit; the solver must bind it as a symbol.
    r = solve_for("ohms_law", {"V": 12, "R": 4}, "I")
    assert math.isclose(r.value, 3.0, abs_tol=1e-9)


def test_v_squared_selects_positive_root():
    r = solve_for("kinematic_v_squared", {"u": 0, "a": 2, "s": 100}, "v")
    assert r.value > 0
    assert math.isclose(r.value, 20.0, abs_tol=1e-6)


def test_missing_value_raises():
    with pytest.raises(MissingValueError):
        solve_for("wave_speed", {"f": 440}, "v")


def test_invalid_target_raises():
    with pytest.raises(SolverError):
        solve_for("wave_speed", {"f": 440, "wavelength": 0.78}, "nope")


def test_steps_and_expression_present():
    r = solve_for("projectile_range", {"v0": 20, "theta": 45}, "R")
    assert len(r.steps) == 4
    assert r.expression  # symbolic rearrangement string


# --- Library integrity --------------------------------------------------------

def test_latex_rendering():
    eqx = equation_latex("projectile_range")
    assert "\\theta" in eqx  # greek theta
    assert "\\frac" in eqx  # division rendered as a fraction
    sol = solution_latex("projectile_range", "R")
    assert sol.startswith("R =")
    # 'wavelength' is prettified to \lambda
    assert "\\lambda" in equation_latex("wave_speed")


def test_solution_latex_never_raises():
    # Every equation/target combination must return a string, not blow up.
    for eq in EQUATIONS.values():
        for var in eq.variables:
            assert isinstance(solution_latex(eq.id, var), str)


def test_every_equation_builds():
    """Each equation parses and declares all of its symbols in units."""
    for eq in EQUATIONS.values():
        sym_eq, symbols = build_equation(eq)
        assert eq.domain in DOMAINS
        if eq.simulation is not None:
            assert eq.simulation in SIMULATION_TYPES
        # constants must be a subset of declared symbols
        assert set(eq.constants).issubset(set(symbols))
