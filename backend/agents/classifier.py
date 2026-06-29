"""Domain classifier — the first LLM step of the pipeline.

Identifies which physics domain a problem belongs to. A keyword heuristic is
used as a fallback if the model's answer is unusable, so the pipeline degrades
gracefully rather than failing outright.
"""
from __future__ import annotations

import logging

from providers import LLMProvider
from solvers.sympy_solver import DOMAIN_INFO, DOMAINS

from .json_utils import parse_json

logger = logging.getLogger(__name__)

_DOMAIN_LIST = "\n".join(
    f"- {d}: {DOMAIN_INFO[d]['description']}" for d in DOMAINS
)

_SYSTEM = (
    "You are a physics problem classifier. Read the problem and choose the "
    "single best-fitting domain from this list:\n"
    f"{_DOMAIN_LIST}\n\n"
    "Respond with ONLY a JSON object of the form "
    '{"domain": "<one of: ' + ", ".join(DOMAINS) + '>"}. No prose.'
)

# Keyword fallback (rough, only used if the LLM answer is unusable).
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "relativity": ("relativ", "dilation", "contraction", "lorentz", "rest energy", "e=mc"),
    "quantum": ("photon", "de broglie", "photoelectric", "quantum", "planck", "energy level", "electron volt"),
    "gravitation": ("orbit", "escape velocity", "gravit", "planet", "satellite", "kepler"),
    "thermodynamics": ("gas", "temperature", "heat", "carnot", "entropy", "mole", "kelvin"),
    "electricity": ("resistor", "ohm", "current", "voltage", "circuit", "capacitor", "watt", "amp"),
    "waves": ("wavelength", "frequency", "refract", "snell", "wave", "hertz", " hz"),
    "fluids": ("buoyan", "bernoulli", "fluid", "density", "pressure at depth", "flow rate"),
    "mechanics": ("projectile", "thrown", "velocity", "force", "momentum", "collision", "pendulum", "spring", "acceler"),
}


def _heuristic(problem: str) -> str:
    text = problem.lower()
    for domain, words in _KEYWORDS.items():
        if any(w in text for w in words):
            return domain
    return "mechanics"


async def classify_domain(provider: LLMProvider, problem: str) -> str:
    """Return the physics domain for ``problem`` (always a valid domain)."""
    try:
        raw = await provider.complete(_SYSTEM, problem)
        data = parse_json(raw)
        domain = str(data.get("domain", "")).strip().lower()
    except Exception as exc:  # noqa: BLE001 - fall back to heuristic
        logger.warning("Classifier LLM/JSON failed (%s); using heuristic.", exc)
        domain = ""

    if domain not in DOMAINS:
        domain = _heuristic(problem)
    return domain
