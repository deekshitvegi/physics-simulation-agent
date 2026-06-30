"""Tolerant JSON extraction from LLM output.

Models often wrap JSON in markdown fences or add a sentence before/after it.
This pulls out the first JSON object regardless of that noise.
"""
from __future__ import annotations

import ast
import json
import operator
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

# Safe arithmetic evaluator — models sometimes emit expressions as JSON values
# (e.g. "r": 2*1.496e11 for "2 AU"), which is invalid JSON.
_ARITH_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_NUMERIC_TOKEN = re.compile(r"^[0-9.eE+\-*/() ]+$")
# A JSON value position: after ':' (object) or ',' / '[' (array), up to the next
# structural char, excluding quoted strings/objects.
_VALUE_RE = re.compile(r"([:,\[]\s*)([^\",}\]\[{]+?)(\s*[,}\]])")


def _safe_arith(expr: str) -> float:
    """Evaluate a pure-arithmetic numeric expression (no names/calls)."""
    node = ast.parse(expr, mode="eval").body

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in _ARITH_OPS:
            return _ARITH_OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ARITH_OPS:
            return _ARITH_OPS[type(n.op)](_eval(n.operand))
        raise ValueError("unsupported expression")

    return float(_eval(node))


def _repair_json_numbers(s: str) -> str:
    """Replace arithmetic expressions in JSON value positions with their value."""

    def repl(m: re.Match) -> str:
        prefix, token, suffix = m.group(1), m.group(2).strip(), m.group(3)
        if _NUMERIC_TOKEN.match(token) and re.search(r"\d", token):
            try:
                return f"{prefix}{_safe_arith(token)}{suffix}"
            except Exception:  # noqa: BLE001 - leave token untouched on failure
                return m.group(0)
        return m.group(0)

    return _VALUE_RE.sub(repl, s)


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
    except json.JSONDecodeError:
        # Repair arithmetic-in-values (e.g. 2*1.496e11) and retry once.
        try:
            data = json.loads(_repair_json_numbers(snippet))
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
