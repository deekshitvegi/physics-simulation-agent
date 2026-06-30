"""Conversational physics/math tutor agent (tool-calling loop).

The LLM converses and tutors; every computation is delegated to the SymPy-backed
tools so the math is exact. Returns the assistant's reply plus any simulation
artifacts the agent chose to render.
"""
from __future__ import annotations

import json
import logging

from providers import LLMProvider

from .tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, ToolError

logger = logging.getLogger(__name__)

MAX_ITERS = 6

_SYSTEM = (
    "You are an expert, friendly physics and math tutor for students. Your goal is "
    "to help them understand, not just hand over answers.\n\n"
    "CRITICAL RULES:\n"
    "- NEVER do arithmetic or solve equations in your head. ALWAYS use the `calculate` "
    "and `solve_equation` tools for EVERY computation — they use an exact computer "
    "algebra system. Doing math yourself causes errors.\n"
    "- Work step by step: identify the physics, state the relevant formula(s), then "
    "call tools to compute. Show the formula and the numbers you plugged in.\n"
    "- When a problem can be visualized, call `show_simulation` so the student sees it.\n"
    "- For multiple-choice questions, reason through EACH option and clearly state which "
    "is/are correct and why.\n"
    "- Be conversational; use earlier messages as context and answer follow-ups.\n\n"
    "ALWAYS present your full worked solution in the reply: state the formula, show the "
    "substituted numbers, and the result of each tool call — like a real physics solution, "
    "not just the final number.\n"
    "FORMATTING: write math in LaTeX — inline as $...$ and display equations as $$...$$ "
    "— so it renders nicely. End with the final answer in bold, including units."
)


async def run_chat(provider: LLMProvider, messages: list[dict]) -> dict:
    """Run the tutor agent over the conversation; return reply + artifacts."""
    work: list[dict] = [{"role": "system", "content": _SYSTEM}, *messages]
    artifacts: list[dict] = []
    last_content = ""

    for _ in range(MAX_ITERS):
        resp = await provider.chat(work, tools=TOOL_SCHEMAS)
        last_content = resp.get("content") or ""
        tool_calls = resp.get("tool_calls") or []

        if not tool_calls:
            return {"reply": last_content, "artifacts": artifacts}

        # Echo the assistant's tool-call message back into the transcript.
        work.append(
            {
                "role": "assistant",
                "content": last_content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls
                ],
            }
        )

        # Execute each tool call and feed results back.
        for tc in tool_calls:
            name = tc["name"]
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            fn = TOOL_FUNCTIONS.get(name)
            if fn is None:
                result = {"error": f"unknown tool '{name}'"}
            else:
                try:
                    result = fn(**args)
                except ToolError as exc:
                    result = {"error": str(exc)}
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Tool %s failed: %s", name, exc)
                    result = {"error": f"{name} failed: {exc}"}

            if name == "show_simulation" and "simulation_type" in result:
                artifacts.append({"type": "simulation", **result})

            work.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": json.dumps(result),
                }
            )

    # Hit the iteration cap — return whatever we have.
    return {
        "reply": last_content or "I wasn't able to finish that — try rephrasing the question.",
        "artifacts": artifacts,
    }
