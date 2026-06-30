"""Explanation generator — the final LLM step.

Turns the deterministic solver result into a friendly, step-by-step narrative.
Because the answer is already computed and validated by SymPy, the explainer is
purely presentational; if it fails, the pipeline falls back to the solver's
own steps so a solve never fails just because the prose call did.
"""
from __future__ import annotations

import logging

from providers import LLMProvider
from solvers.equations import get_equation
from solvers.sympy_solver import SolveResult

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a friendly physics tutor. Given a problem and its already-solved, "
    "verified result, write a short explanation (3-4 sentences) in clear, natural "
    "English for a student.\n"
    "Style rules:\n"
    "- Write in prose. Do NOT use programming syntax for math: never write '**', "
    "'*', or '/'. Say 'squared', 'multiplied by', 'divided by', or name the quantity.\n"
    "- Refer to the formula by its name and describe what each quantity means.\n"
    "- State the final numeric answer in words once.\n"
    "- Do NOT change the computed answer or invent new values. Plain text only."
)


def _fallback(problem: str, result: SolveResult) -> str:
    return " ".join(result.steps)


async def explain(
    provider: LLMProvider, problem: str, result: SolveResult, domain: str
) -> str:
    """Return a plain-English explanation, falling back to solver steps on error."""
    eq = get_equation(result.equation_id)
    subs = ", ".join(f"{k} = {v}" for k, v in result.substitutions.items())
    user = (
        f"Problem: {problem}\n"
        f"Domain: {domain}\n"
        f"Equation used: {eq.name} ({eq.formula})\n"
        f"Known values: {subs}\n"
        f"Solved for {result.target} = {result.value} {result.unit}\n"
        f"Computed steps:\n- " + "\n- ".join(result.steps)
    )
    try:
        text = await provider.complete(_SYSTEM, user)
        return text.strip() or _fallback(problem, result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Explainer failed (%s); using solver steps.", exc)
        return _fallback(problem, result)
