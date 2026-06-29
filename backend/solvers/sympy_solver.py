"""Symbolic physics solver built on SymPy.

This module is intentionally LLM-free: given an equation id (selected by the
agent), a dict of known numeric values, and a target symbol to solve for, it
rearranges and evaluates the equation **symbolically** and validates the result
by back-substitution. No answer is ever produced by a language model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import floor, log10

import sympy as sp

from .equations import (
    DOMAIN_INFO,
    DOMAINS,
    SIMULATION_TYPES,
    Equation,
    catalog,
    get_equation,
)

__all__ = [
    "SolveResult",
    "SolverError",
    "MissingValueError",
    "solve_for",
    "catalog",
    "get_equation",
    "equation_latex",
    "solution_latex",
    "DOMAINS",
    "DOMAIN_INFO",
    "SIMULATION_TYPES",
]


class SolverError(Exception):
    """Raised when an equation cannot be solved or fails validation."""


class MissingValueError(SolverError):
    """Raised when required known values are not supplied."""


# Functions/constants allowed inside equation strings. Symbol names are bound
# explicitly per-equation (see ``build_equation``) so they always win over any
# same-named SymPy global (e.g. ``I`` would otherwise be the imaginary unit).
_FUNC_NS: dict[str, object] = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sqrt": sp.sqrt, "exp": sp.exp, "log": sp.log, "Abs": sp.Abs,
    "pi": sp.pi,
}


@dataclass
class SolveResult:
    equation_id: str
    target: str
    value: float
    unit: str
    expression: str
    substitutions: dict[str, float]
    steps: list[str]
    simulation: str | None = None

    def to_dict(self) -> dict:
        return {
            "equation_id": self.equation_id,
            "target": self.target,
            "value": self.value,
            "unit": self.unit,
            "expression": self.expression,
            "substitutions": self.substitutions,
            "steps": self.steps,
            "simulation": self.simulation,
        }


# Multi-letter symbol names SymPy doesn't render as Greek/operators on its own.
_LATEX_PRETTY = {"wavelength": r"\lambda", "dT": r"\Delta T", "Vol": "V"}


def _pretty_latex(s: str) -> str:
    for raw, pretty in _LATEX_PRETTY.items():
        s = s.replace(raw, pretty)
    return s


def _build_display(eq_def: Equation) -> tuple[sp.Expr, sp.Expr, dict[str, sp.Symbol]]:
    """Parse an equation's display forms (no degree->radian noise) for LaTeX."""
    symbols = {name: sp.Symbol(name) for name in eq_def.units}
    local_ns = {**symbols, **_FUNC_NS}
    lhs = sp.sympify(eq_def.display_lhs or eq_def.lhs, locals=local_ns)
    rhs = sp.sympify(eq_def.display_rhs or eq_def.rhs, locals=local_ns)
    return lhs, rhs, symbols


def equation_latex(equation_id: str) -> str:
    """LaTeX of the equation as written (e.g. ``R = \\frac{v_0^2 \\sin{2\\theta}}{g}``)."""
    eq_def = get_equation(equation_id)
    try:
        lhs, rhs, _ = _build_display(eq_def)
        return _pretty_latex(sp.latex(sp.Eq(lhs, rhs)))
    except Exception:  # noqa: BLE001 - display is best-effort
        return eq_def.display_formula


def solution_latex(equation_id: str, target: str) -> str:
    """LaTeX of ``target = <rearranged expression>`` for the solved variable."""
    eq_def = get_equation(equation_id)
    try:
        lhs, rhs, symbols = _build_display(eq_def)
        if target not in symbols:
            return _pretty_latex(sp.latex(sp.Symbol(target)))
        sols = sp.solve(sp.Eq(lhs, rhs), symbols[target])
        if not sols:
            return _pretty_latex(sp.latex(rhs))
        return _pretty_latex(f"{sp.latex(symbols[target])} = {sp.latex(sols[0])}")
    except Exception:  # noqa: BLE001 - display is best-effort
        return f"{target} = ?"


def build_equation(eq_def: Equation) -> tuple[sp.Equality, dict[str, sp.Symbol]]:
    """Parse an :class:`Equation` definition into a SymPy ``Eq`` and symbol map."""
    symbols = {name: sp.Symbol(name) for name in eq_def.units}
    local_ns = {**symbols, **_FUNC_NS}
    lhs = sp.sympify(eq_def.lhs, locals=local_ns)
    rhs = sp.sympify(eq_def.rhs, locals=local_ns)
    eq = sp.Eq(lhs, rhs)

    # Data sanity check: every free symbol must be declared in ``units``.
    extra = eq.free_symbols - set(symbols.values())
    if extra:
        names = ", ".join(sorted(str(s) for s in extra))
        raise SolverError(
            f"Equation '{eq_def.id}' references undeclared symbol(s): {names}. "
            "Add them to the equation's units."
        )
    return eq, symbols


def _round_sig(x: float, sig: int = 6) -> float:
    if x == 0 or not _is_finite(x):
        return float(x)
    digits = sig - int(floor(log10(abs(x)))) - 1
    return round(x, digits)


def _is_finite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


def _fmt(x: float) -> str:
    r = _round_sig(float(x), 6)
    if r == int(r) and abs(r) < 1e15:
        return str(int(r))
    return f"{r:g}"


def _select_solution(solutions: list) -> float | None:
    """Pick the physically meaningful root: prefer the smallest non-negative real."""
    reals: list[float] = []
    for sol in solutions:
        try:
            c = complex(sp.N(sol))
        except (TypeError, ValueError):
            continue
        if abs(c.imag) < 1e-9 and _is_finite(c.real):
            reals.append(c.real)
    if not reals:
        return None
    positives = [r for r in reals if r >= -1e-12]
    return min(positives) if positives else max(reals)


def solve_for(
    equation_id: str,
    knowns: dict[str, float],
    target: str,
) -> SolveResult:
    """Solve ``equation_id`` for ``target`` given ``knowns``.

    Args:
        equation_id: Key into the equation library.
        knowns: Mapping of symbol name -> numeric value supplied by the caller.
        target: The symbol to solve for.

    Returns:
        A validated :class:`SolveResult`.

    Raises:
        MissingValueError: a required value (and no constant default) is missing.
        SolverError: target invalid, no real solution, or validation failed.
    """
    eq_def = get_equation(equation_id)
    eq, symbols = build_equation(eq_def)

    if target not in symbols:
        raise SolverError(
            f"'{target}' is not a variable of '{equation_id}'. "
            f"Valid: {', '.join(symbols)}"
        )
    target_sym = symbols[target]

    subs: dict[sp.Symbol, sp.Float] = {}
    used: dict[str, float] = {}
    missing: list[str] = []
    for name, sym in symbols.items():
        if name == target:
            continue
        if knowns.get(name) is not None:
            val = float(knowns[name])
            subs[sym] = sp.Float(val)
            used[name] = val
        elif name in eq_def.constants:
            val = float(eq_def.constants[name])
            subs[sym] = sp.Float(val)
            used[name] = val
        else:
            missing.append(name)
    if missing:
        raise MissingValueError(
            f"Missing value(s) {missing} to solve '{equation_id}' for '{target}'."
        )

    # Symbolic rearrangement for display (before plugging in numbers).
    try:
        symbolic = sp.solve(eq, target_sym)
        expression = str(symbolic[0]) if symbolic else eq_def.formula
    except Exception:
        expression = eq_def.formula

    # Numeric solve.
    substituted = eq.subs(subs)
    try:
        solutions = sp.solve(substituted, target_sym)
    except Exception as exc:  # noqa: BLE001
        raise SolverError(f"SymPy failed to solve '{equation_id}': {exc}") from exc

    value = _select_solution(solutions)
    if value is None:
        raise SolverError(f"No real solution for '{target}' in '{equation_id}'.")

    # Validate by back-substitution. Substituting into an Eq collapses it to a
    # boolean, so evaluate the residual of (lhs - rhs) as an expression instead.
    full_subs = dict(subs)
    full_subs[target_sym] = sp.Float(value)
    try:
        residual = abs(float((eq.lhs - eq.rhs).subs(full_subs)))
        scale = max(1.0, abs(float(eq.rhs.subs(full_subs))))
    except (TypeError, ValueError) as exc:
        raise SolverError(f"Validation could not be evaluated: {exc}") from exc
    if residual > 1e-6 * scale:
        raise SolverError(
            f"Solution failed validation for '{equation_id}' "
            f"(residual={residual:.3g})."
        )

    value = _round_sig(value, 6)
    unit = eq_def.units.get(target, "")
    subs_str = ", ".join(f"{k}={_fmt(v)}" for k, v in used.items())
    steps = [
        f"Identified relation: {eq_def.name} ({eq_def.formula}).",
        f"Rearrange for {target}: {target} = {expression}.",
        f"Substitute known values: {subs_str}." if subs_str else "No substitutions needed.",
        f"Result: {target} = {_fmt(value)} {unit}".strip() + ".",
    ]

    return SolveResult(
        equation_id=equation_id,
        target=target,
        value=value,
        unit=unit,
        expression=expression,
        substitutions=used,
        steps=steps,
        simulation=eq_def.simulation,
    )
