"""Physics agent pipeline orchestrator.

Ties the steps together:

    classify domain (LLM)
        -> extract equation + variables (LLM)
            -> solve symbolically (SymPy, exact)
                -> map to a simulation template (deterministic)
                    -> explain (LLM, presentational)

Only ``solve`` (the full pipeline) needs the LLM. ``resolve`` re-runs the math
for slider updates with no LLM calls at all.
"""
from __future__ import annotations

import logging

from providers import LLMProvider
from solvers.equations import get_equation
from solvers.sympy_solver import (
    SolveResult,
    equation_latex,
    solution_latex,
    solve_for,
)

from .classifier import classify_domain
from .explainer import explain
from .extractor import extract_solution_plan

logger = logging.getLogger(__name__)


# --- Simulation mapping (deterministic) --------------------------------------

def _num(values: dict, *names: str, default=None):
    """First present, non-None value among ``names``."""
    for n in names:
        v = values.get(n)
        if v is not None:
            return v
    return default


def map_simulation(
    result: SolveResult, knowns: dict[str, float]
) -> tuple[str | None, dict]:
    """Map a solved equation to a simulation type and its parameters."""
    sim = result.simulation
    if sim is None:
        return None, {}

    values = {**knowns, result.target: result.value}

    if sim == "projectile":
        return sim, {
            "v0": _num(values, "v0", default=20.0),
            "angle": _num(values, "theta", "angle", default=45.0),
            "g": _num(values, "g", default=9.81),
        }
    if sim == "pendulum":
        return sim, {
            "length": _num(values, "L", "m", default=1.0) if result.equation_id != "spring_period" else 1.0,
            "g": _num(values, "g", default=9.81),
            "angle": _num(values, "theta", "angle", default=30.0),
            "period": _num(values, "T", default=None),
        }
    if sim == "wave":
        return sim, {
            "frequency": _num(values, "f", default=1.0),
            "wavelength": _num(values, "wavelength", default=1.0),
            "amplitude": _num(values, "amplitude", "A", default=1.0),
            "speed": _num(values, "v", default=None),
        }
    if sim == "circuit":
        circuit_type = (
            "series" if result.equation_id == "resistors_series"
            else "parallel" if result.equation_id == "resistors_parallel"
            else "single"
        )
        return sim, {
            "circuitType": circuit_type,
            "voltage": _num(values, "V", default=None),
            "current": _num(values, "I", default=None),
            "resistance": _num(values, "R", default=None),
            "r1": _num(values, "R1", default=None),
            "r2": _num(values, "R2", default=None),
        }
    if sim == "orbital":
        return sim, {
            "mass": _num(values, "M", default=5.972e24),
            "radius": _num(values, "r", default=6.371e6),
            "velocity": _num(values, "v", default=None),
        }
    if sim == "collision":
        return sim, {
            "m1": _num(values, "m1", default=1.0),
            "m2": _num(values, "m2", default=1.0),
            "u1": _num(values, "u1", default=1.0),
            "u2": _num(values, "u2", default=0.0),
            "v1f": _num(values, "v1f", default=None),
            "v2f": _num(values, "v2f", default=None),
        }
    return sim, dict(values)


# --- Response assembly --------------------------------------------------------

def build_response(
    domain: str,
    plan: dict,
    result: SolveResult,
    sim_type: str | None,
    sim_params: dict,
    explanation: str,
) -> dict:
    eq = get_equation(result.equation_id)
    inputs = [
        {"name": name, "value": value, "unit": eq.units.get(name, "")}
        for name, value in result.substitutions.items()
    ]
    return {
        "domain": domain,
        "equation_id": result.equation_id,
        "equation_name": eq.name,
        "target": result.target,
        "variables": dict(result.substitutions),
        "inputs": inputs,
        "equations": [eq.formula, f"{result.target} = {result.expression}"],
        "equation_latex": equation_latex(result.equation_id),
        "answer": {
            "value": result.value,
            "unit": result.unit,
            "expression": result.expression,
            "latex": solution_latex(result.equation_id, result.target),
        },
        "simulation_type": sim_type,
        "simulation_params": sim_params,
        "steps": result.steps,
        "derivation": result.derivation,
        "explanation": explanation,
    }


# --- The agent ----------------------------------------------------------------

class PhysicsAgent:
    """Runs the full classify -> extract -> solve -> map -> explain pipeline."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def solve(self, problem: str) -> dict:
        problem = (problem or "").strip()
        if not problem:
            raise ValueError("Problem text is empty.")

        domain = await classify_domain(self.provider, problem)
        plan = await extract_solution_plan(self.provider, problem, domain)
        result = solve_for(plan["equation_id"], plan["knowns"], plan["target"])
        sim_type, sim_params = map_simulation(result, plan["knowns"])
        explanation = await explain(self.provider, problem, result, plan["domain"])
        return build_response(
            plan["domain"], plan, result, sim_type, sim_params, explanation
        )

    @staticmethod
    def resolve(equation_id: str, target: str, knowns: dict[str, float]) -> dict:
        """Re-solve with new values for slider updates — pure math, no LLM."""
        result = solve_for(equation_id, knowns, target)
        sim_type, sim_params = map_simulation(result, knowns)
        eq = get_equation(equation_id)
        return {
            "equation_id": equation_id,
            "target": target,
            "variables": dict(result.substitutions),
            "answer": {
                "value": result.value,
                "unit": result.unit,
                "expression": result.expression,
                "latex": solution_latex(equation_id, target),
            },
            "simulation_type": sim_type,
            "simulation_params": sim_params,
            "steps": result.steps,
            "derivation": result.derivation,
            "equations": [eq.formula, f"{target} = {result.expression}"],
            "equation_latex": equation_latex(equation_id),
        }
