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
    "COMPUTATION — never guess:\n"
    "- NEVER do arithmetic or solve equations in your head. ALWAYS use the `calculate` "
    "and `solve_equation` tools for EVERY computation. Show the formula and the numbers.\n\n"
    "BE TRUTHFUL, NOT AGREEABLE — this is critical:\n"
    "- Do NOT change your answer just because the student disagrees or asserts that "
    "something is true or false. Re-derive it from physics first principles.\n"
    "- If the student is genuinely right, acknowledge it. If the student is WRONG, "
    "respectfully HOLD YOUR GROUND and explain why. Never flip-flop to please them — "
    "a tutor who agrees with everything is useless and untrustworthy.\n"
    "- For multiple-choice questions, evaluate EACH option independently from first "
    "principles, then commit to which is/are correct.\n\n"
    "HONESTY ABOUT CONFIDENCE:\n"
    "- When an answer comes from a tool computation it is exact — say so. When it is "
    "conceptual reasoning with no computation, make clear it is your best reasoning, "
    "not a verified calculation.\n\n"
    "SIMULATIONS — use sparingly:\n"
    "- Only call `show_simulation` when the problem is GENUINELY a projectile, pendulum, "
    "wave, electrical circuit, orbiting body, or collision, AND gives concrete numbers.\n"
    "- Do NOT show a simulation for conceptual questions or MCQs about principles. "
    "NEVER invent parameters.\n\n"
    "Present the full worked solution. FORMATTING: math in LaTeX — inline $...$ and display "
    "$$...$$. End with the final answer in bold, with units."
)


def _to_provider_message(m: dict) -> dict:
    """Convert an incoming message to provider format, inlining any images."""
    images = m.get("images")
    if images:
        content: list[dict] = [{"type": "text", "text": m.get("content", "")}]
        for url in images:
            content.append({"type": "image_url", "image_url": {"url": url}})
        return {"role": m["role"], "content": content}
    return {"role": m["role"], "content": m.get("content", "")}


async def run_chat(provider: LLMProvider, messages: list[dict]) -> dict:
    """Run the tutor agent over the conversation; return reply + artifacts."""
    work: list[dict] = [
        {"role": "system", "content": _SYSTEM},
        *(_to_provider_message(m) for m in messages),
    ]
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
