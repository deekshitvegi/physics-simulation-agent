"""Deterministic tools the tutor agent can call.

The LLM never computes — it calls these. ``calculate`` and ``solve_equation``
run SymPy (exact), and ``show_simulation`` hands a visualization to the UI.
Each tool returns a JSON-serializable dict and is exposed to the model via an
OpenAI/Groq-style function schema.
"""
from __future__ import annotations

import sympy as sp

from solvers.equations import EQUATIONS, SIMULATION_TYPES
from solvers.sympy_solver import SolverError, catalog, solve_for

# Safe namespace for parsing expressions: math functions + common constants.
_SAFE_NS: dict[str, object] = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sqrt": sp.sqrt, "exp": sp.exp, "log": sp.log, "ln": sp.log,
    "Abs": sp.Abs, "pi": sp.pi, "E": sp.E,
}


class ToolError(Exception):
    """Raised when a tool is called with invalid arguments."""


def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression exactly via SymPy."""
    try:
        expr = sp.sympify(expression, locals=_SAFE_NS)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"Could not parse expression: {exc}") from exc

    result: dict = {"expression": expression, "exact": str(expr)}
    if not expr.free_symbols:
        try:
            result["value"] = float(sp.N(expr))
        except (TypeError, ValueError):
            result["value"] = str(sp.N(expr))
    else:
        result["free_symbols"] = sorted(str(s) for s in expr.free_symbols)
    return result


def solve_equation(equation: str, variable: str) -> dict:
    """Symbolically solve an equation (or 'expr = 0') for a variable."""
    try:
        if "=" in equation:
            lhs_s, rhs_s = equation.split("=", 1)
            eq = sp.Eq(sp.sympify(lhs_s, locals=_SAFE_NS), sp.sympify(rhs_s, locals=_SAFE_NS))
        else:
            eq = sp.sympify(equation, locals=_SAFE_NS)
        var = sp.Symbol(variable)
        solutions = sp.solve(eq, var)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"Could not solve '{equation}' for '{variable}': {exc}") from exc

    out = []
    for s in solutions:
        item = {"exact": str(s)}
        if not s.free_symbols:
            try:
                item["value"] = float(sp.N(s))
            except (TypeError, ValueError):
                item["value"] = str(sp.N(s))
        out.append(item)
    return {"equation": equation, "variable": variable, "solutions": out}


def show_simulation(simulation_type: str, params: dict | None = None) -> dict:
    """Validate a simulation request to render in the UI."""
    if simulation_type not in SIMULATION_TYPES:
        raise ToolError(
            f"Unknown simulation '{simulation_type}'. Options: {', '.join(SIMULATION_TYPES)}"
        )
    clean: dict = {}
    for key, value in (params or {}).items():
        try:
            clean[key] = float(value)
        except (TypeError, ValueError):
            clean[key] = value
    return {"simulation_type": simulation_type, "simulation_params": clean}


def list_formulas(domain: str | None = None) -> dict:
    """List vetted equations from the curated library (optionally by domain)."""
    return {"formulas": catalog(domain)}


def solve_with_formula(
    equation_id: str, target: str, knowns: dict | None = None
) -> dict:
    """Solve a problem using a VETTED library formula — correct + exact."""
    if equation_id not in EQUATIONS:
        raise ToolError(
            f"Unknown equation_id '{equation_id}'. Call list_formulas first to see valid ids."
        )
    try:
        result = solve_for(equation_id, knowns or {}, target)
    except SolverError as exc:
        raise ToolError(str(exc)) from exc
    return {
        "equation_id": equation_id,
        "target": target,
        "value": result.value,
        "unit": result.unit,
        "formula": EQUATIONS[equation_id].display_formula,
        "derivation": result.derivation,
        "simulation_type": result.simulation,
    }


# --- Tool registry + JSON schemas (OpenAI/Groq function-calling format) -------

TOOL_FUNCTIONS = {
    "calculate": calculate,
    "solve_equation": solve_equation,
    "list_formulas": list_formulas,
    "solve_with_formula": solve_with_formula,
    "show_simulation": show_simulation,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Evaluate a math expression EXACTLY with a computer algebra system. "
                "Use this for ALL arithmetic — never compute in your head. Angles are "
                "in radians (use pi, e.g. sin(pi/4)). Available: + - * / ** , sqrt, sin, "
                "cos, tan, asin, acos, atan, exp, log/ln, pi, E."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "e.g. '492*2*2/(330-2)' or 'sqrt(2*6.674e-11*5.972e24/6.371e6)'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_equation",
            "description": "Symbolically solve an equation for a variable, e.g. equation='v**2 = u**2 + 2*a*s', variable='v'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equation": {"type": "string"},
                    "variable": {"type": "string"},
                },
                "required": ["equation", "variable"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_formulas",
            "description": (
                "List vetted physics formulas from the curated library (id, formula, "
                "variables). Use this to find the correct formula for standard textbook "
                "quantities. Optionally filter by domain: mechanics, waves, electricity, "
                "thermodynamics, gravitation, fluids, quantum, relativity."
            ),
            "parameters": {
                "type": "object",
                "properties": {"domain": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_with_formula",
            "description": (
                "Solve using a VETTED library formula — guarantees the correct formula AND "
                "exact arithmetic. Prefer this over recalling formulas from memory. First "
                "use list_formulas to find the equation_id and its variable names; pass the "
                "target variable to solve for and the known numeric values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "equation_id": {"type": "string"},
                    "target": {"type": "string"},
                    "knowns": {"type": "object"},
                },
                "required": ["equation_id", "target", "knowns"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_simulation",
            "description": (
                "Render a live interactive simulation for the student. Angles here are in "
                "DEGREES (not radians). simulation_type is one of: projectile (v0 m/s, angle "
                "deg, g), pendulum (length m, g, angle deg), wave (frequency Hz, wavelength m, "
                "amplitude), circuit (circuitType 'series'/'parallel'/'single', r1, r2, voltage, "
                "current), orbital (mass kg, radius m, velocity m/s), collision (m1, m2, u1, u2)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_type": {"type": "string"},
                    "params": {"type": "object"},
                },
                "required": ["simulation_type", "params"],
            },
        },
    },
]
