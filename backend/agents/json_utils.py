"""Tolerant JSON extraction from LLM output.

Models often wrap JSON in markdown fences or add a sentence before/after it.
This pulls out the first JSON object regardless of that noise.
"""
from __future__ import annotations

import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def parse_json(text: str) -> dict:
    """Extract and parse the first JSON object found in ``text``.

    Raises:
        ValueError: if no parseable JSON object is present.
    """
    if not text or not text.strip():
        raise ValueError("Empty response; no JSON to parse.")

    candidate = text.strip()
    fence = _FENCE.search(candidate)
    if fence:
        candidate = fence.group(1).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in response: {text[:200]!r}")

    snippet = candidate[start : end + 1]
    try:
        data = json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}; raw={snippet[:200]!r}") from exc

    if not isinstance(data, dict):
        raise ValueError("Parsed JSON is not an object.")
    return data


def coerce_float(value) -> float | None:
    """Best-effort conversion of an LLM-provided value to float, else None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        # strip a trailing unit if present, keep leading number (e.g. "20 m/s")
        match = re.match(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None
