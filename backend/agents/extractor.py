"""Variable extractor + equation selector — the second LLM step.

Given the problem and the candidate equations for its domain, the LLM picks the
single best equation, the unknown to solve for, and the known numeric values
(using the equation's exact variable names). The numbers are then handed to the
SymPy solver — the LLM never computes the answer.
"""
from __future__ import annotations

import logging

from providers import LLMProvider
from solvers.equations import EQUATIONS
from solvers.sympy_solver import catalog

from .json_utils import coerce_float, parse_json

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when a usable solution plan cannot be extracted."""


def _format_catalog(entries: list[dict]) -> str:
    lines = []
    for e in entries:
        vars_str = ", ".join(f"{n} ({u or 'dimensionless'})" for n, u in e["variables"].items())
        consts = f"  [auto-filled constants: {', '.join(e['constants'])}]" if e["constants"] else ""
        lines.append(
            f"- id: {e['id']}\n"
            f"    formula: {e['formula']}\n"
            f"    description: {e['description']}\n"
            f"    variables: {vars_str}{consts}"
        )
    return "\n".join(lines)


_SYSTEM = (
    "You convert a physics word problem into a precise solution plan. "
    "You are given candidate equations. Do the following:\n"
    "1. Choose the SINGLE best equation by its id.\n"
    "2. Choose the target: the one variable the problem asks you to find.\n"
    "3. Provide knowns: a JSON object mapping the equation's variable names to "
    "numeric values taken from the problem.\n\n"
    "Rules:\n"
    "- Use the EXACT variable names from the chosen equation.\n"
    "- Angles must be in degrees. All other quantities in SI base units unless "
    "the variable's unit hint says otherwise (e.g. combined gas law keeps atm/L).\n"
    "- Convert units as needed (km -> m, grams -> kg, etc.).\n"
    "- Do NOT include the target variable in knowns.\n"
    "- Do NOT include constants that are listed as auto-filled.\n"
    "- Each value MUST be a single JSON number you have already computed. Never "
    "write arithmetic or units (e.g. for 2 AU write 2.992e11, NOT 2*1.496e11).\n"
    "- For well-known bodies, supply the numbers (Earth mass 5.972e24 kg, "
    "Earth radius 6.371e6 m, etc.).\n"
    'Respond with ONLY JSON: {"equation_id": "...", "target": "...", '
    '"knowns": {"name": number, ...}}. No prose.'
)


async def _extract_once(
    provider: LLMProvider, problem: str, entries: list[dict]
) -> dict:
    user = (
        f"Problem: {problem}\n\n"
        f"Candidate equations:\n{_format_catalog(entries)}"
    )
    raw = await provider.complete(_SYSTEM, user)
    data = parse_json(raw)

    equation_id = str(data.get("equation_id", "")).strip()
    target = str(data.get("target", "")).strip()
    knowns_raw = data.get("knowns", {}) or {}

    if equation_id not in EQUATIONS:
        raise ExtractionError(f"Model chose unknown equation id: {equation_id!r}")

    eq = EQUATIONS[equation_id]
    if target not in eq.variables:
        raise ExtractionError(
            f"Target {target!r} is not a variable of {equation_id!r} "
            f"(valid: {', '.join(eq.variables)})"
        )

    # Coerce, drop the target if echoed, drop unknown keys and nulls.
    knowns: dict[str, float] = {}
    for name, value in knowns_raw.items():
        if name == target or name not in eq.units:
            continue
        f = coerce_float(value)
        if f is not None:
            knowns[name] = f

    return {"equation_id": equation_id, "target": target, "knowns": knowns}


async def extract_solution_plan(
    provider: LLMProvider, problem: str, domain: str
) -> dict:
    """Extract {equation_id, target, knowns, domain}.

    Tries the domain's equations first; if that yields no usable plan (e.g. the
    domain was misclassified), retries once against the full catalog.
    """
    domain_entries = catalog(domain)
    try:
        plan = await _extract_once(provider, problem, domain_entries)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Domain-scoped extraction failed (%s); retrying full catalog.", exc)
        plan = await _extract_once(provider, problem, catalog())

    plan["domain"] = EQUATIONS[plan["equation_id"]].domain
    return plan
