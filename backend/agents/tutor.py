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

MAX_ITERS = 8

_SYSTEM = (
    "You are an expert, friendly physics and math tutor for students. Your goal is "
    "to help them understand, not just hand over answers.\n\n"
    "COMPUTATION — never guess:\n"
    "- NEVER do arithmetic or solve equations in your head. ALWAYS use the tools for EVERY "
    "computation. Show the formula and the numbers.\n"
    "- PREFER vetted formulas: for standard textbook quantities, call `list_formulas` to "
    "find the right one, then `solve_with_formula` — this guarantees the correct formula. "
    "Use `calculate` / `solve_equation` only for steps no library formula covers.\n\n"
    "RESEARCH strategy for exam/known problems:\n"
    "1. Call `search_web` using the EXACT wording of the problem — this finds the published "
    "problem and its solution with few, precise matches. Then `fetch_url` the best solution "
    "source (prefer official papers / solution sites) and READ it.\n"
    "2. From the source, identify the correct METHOD and formula(s).\n"
    "3. IMPORTANT — if the student's numbers DIFFER from the source's, do NOT copy the "
    "source's answer. Re-apply the same method to the STUDENT's actual values using "
    "`calculate` / `solve_with_formula` so the arithmetic is exact and correct.\n"
    "4. If it's conceptual (no numbers to compute), report the source's answer. Always CITE "
    "the source URL. Web sources can be wrong — cross-check before trusting them.\n\n"
    "BE TRUTHFUL, NOT AGREEABLE — this is critical:\n"
    "- Do NOT change your answer just because the student disagrees or asserts that "
    "something is true or false. Re-derive it from physics first principles.\n"
    "- If the student is genuinely right, acknowledge it. If the student is WRONG, "
    "respectfully HOLD YOUR GROUND and explain why. Never flip-flop to please them — "
    "a tutor who agrees with everything is useless and untrustworthy.\n"
    "- For multiple-choice questions, evaluate EACH option independently from first "
    "principles, then commit to which is/are correct.\n\n"
    "HONESTY GATE — never bluff:\n"
    "- If a problem needs methods beyond your tools, or you are genuinely unsure, SAY SO "
    "plainly: state that you can't solve it reliably and what it would take. Do NOT invent "
    "a confident answer.\n"
    "- When an answer comes from a tool computation it is exact — say so. When it is "
    "conceptual reasoning with no computation, state clearly that it is your reasoning, "
    "not a verified calculation, and that the student should double-check.\n\n"
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


_TRANSCRIBE_SYSTEM = (
    "You transcribe a physics or math problem from an image into plain text. "
    "Include EVERY number, exponent (write powers like 10^-2), unit, symbol, and all "
    "answer options exactly as shown. Output ONLY the transcribed problem — no solution, "
    "no commentary."
)


async def _transcribe_image(provider: LLMProvider, image_msg: dict) -> str:
    """Use the vision model to read an image into clean problem text."""
    try:
        resp = await provider.chat(
            [{"role": "system", "content": _TRANSCRIBE_SYSTEM}, image_msg],
            tools=None,
        )
        return (resp.get("content") or "").strip()
    except Exception:  # noqa: BLE001 - transcription is best-effort
        return ""


async def run_chat(provider: LLMProvider, messages: list[dict]) -> dict:
    """Run the tutor agent over the conversation; return reply + artifacts."""
    # Transcribe any images to clean text first (vision model), so the main
    # tool-calling + web-search loop runs on an accurate problem statement.
    prepared: list[dict] = []
    for m in messages:
        pm = _to_provider_message(m)
        if isinstance(pm.get("content"), list):
            transcription = await _transcribe_image(provider, pm)
            base = (m.get("content") or "").strip()
            if transcription:
                prepared.append(
                    {
                        "role": m["role"],
                        "content": f"{base}\n\nProblem (read from the image):\n{transcription}".strip(),
                    }
                )
            else:
                prepared.append(pm)  # fall back to sending the image directly
        else:
            prepared.append(pm)

    work: list[dict] = [{"role": "system", "content": _SYSTEM}, *prepared]
    artifacts: list[dict] = []
    sources: dict[str, dict] = {}  # url -> {title, url, read}
    last_content = ""
    computed = False  # True once an exact-math tool is used (verification signal)

    for _ in range(MAX_ITERS):
        resp = await provider.chat(work, tools=TOOL_SCHEMAS)
        last_content = resp.get("content") or ""
        tool_calls = resp.get("tool_calls") or []

        if not tool_calls:
            return {
                "reply": last_content,
                "artifacts": artifacts,
                "verified": computed,
                "sources": list(sources.values()),
            }

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
            if name in ("calculate", "solve_equation", "solve_with_formula"):
                computed = True
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
            if name == "search_web" and isinstance(result, dict):
                for hit in result.get("results", []):
                    u = hit.get("url")
                    if u:
                        sources.setdefault(u, {"title": hit.get("title", u), "url": u, "read": False})
            if name == "fetch_url" and isinstance(result, dict):
                u = result.get("url")
                if u:
                    sources.setdefault(u, {"title": u, "url": u, "read": True})
                    sources[u]["read"] = True

            work.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": json.dumps(result),
                }
            )

    # Hit the iteration cap — force a final answer (no more tools) from context.
    try:
        final = await provider.chat(work, tools=None)
        reply = (final.get("content") or "").strip()
    except Exception:  # noqa: BLE001
        reply = ""
    return {
        "reply": reply or last_content or "I couldn't fully solve this one — try rephrasing it.",
        "artifacts": artifacts,
        "verified": computed,
        "sources": list(sources.values()),
    }
