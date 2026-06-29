"""Pipeline tests using a scripted provider (no real LLM calls).

The scripted provider returns canned responses in order, letting us verify the
full classify -> extract -> solve -> map -> explain orchestration deterministically.
"""
import pytest

from agents import PhysicsAgent, classify_domain, extract_solution_plan
from agents.json_utils import coerce_float, parse_json
from providers import LLMProvider


class ScriptedProvider(LLMProvider):
    name = "scripted"

    def __init__(self, responses):
        super().__init__("dummy-key", "scripted-model")
        self._responses = list(responses)
        self.calls = []

    async def _generate(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self._responses.pop(0)


# --- Full pipeline ------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_projectile_end_to_end():
    provider = ScriptedProvider([
        '{"domain": "mechanics"}',
        '{"equation_id": "projectile_range", "target": "R", "knowns": {"v0": 20, "theta": 45}}',
        "The ball is a projectile; using R = v0^2*sin(2*theta)/g it travels about 40.8 m.",
    ])
    agent = PhysicsAgent(provider)
    resp = await agent.solve("A ball is thrown at 45 degrees with 20 m/s, how far does it travel?")

    assert resp["domain"] == "mechanics"
    assert resp["equation_id"] == "projectile_range"
    assert resp["answer"]["unit"] == "m"
    assert abs(resp["answer"]["value"] - 40.8) < 0.5
    assert resp["simulation_type"] == "projectile"
    assert resp["simulation_params"]["v0"] == 20
    assert resp["simulation_params"]["angle"] == 45
    assert resp["explanation"]
    assert len(resp["steps"]) == 4
    assert len(provider.calls) == 3  # classify, extract, explain


@pytest.mark.asyncio
async def test_explainer_failure_falls_back_to_steps():
    # Only 2 responses -> the explain call raises (pop from empty), pipeline
    # must still succeed using solver steps.
    provider = ScriptedProvider([
        '{"domain": "waves"}',
        '{"equation_id": "wave_speed", "target": "v", "knowns": {"f": 440, "wavelength": 0.78}}',
    ])
    agent = PhysicsAgent(provider)
    resp = await agent.solve("A wave has frequency 440 Hz and wavelength 0.78 m. What is its speed?")
    assert abs(resp["answer"]["value"] - 343.2) < 0.1
    assert resp["explanation"]  # fallback explanation present
    assert resp["simulation_type"] == "wave"


# --- resolve (slider re-solve, no LLM) ---------------------------------------

def test_resolve_no_llm():
    out = PhysicsAgent.resolve("projectile_range", "R", {"v0": 30, "theta": 30})
    assert abs(out["answer"]["value"] - 79.45) < 0.5
    assert out["simulation_params"]["v0"] == 30
    assert out["simulation_params"]["angle"] == 30


# --- Component-level ----------------------------------------------------------

@pytest.mark.asyncio
async def test_extractor_coerces_units_and_strips_target():
    provider = ScriptedProvider([
        '{"equation_id": "wave_speed", "target": "v", "knowns": {"f": "440 Hz", "wavelength": 0.78, "v": 999}}',
    ])
    plan = await extract_solution_plan(provider, "wave problem", "waves")
    assert plan["equation_id"] == "wave_speed"
    assert plan["knowns"]["f"] == 440.0
    assert "v" not in plan["knowns"]  # echoed target dropped


@pytest.mark.asyncio
async def test_classifier_heuristic_fallback_on_bad_json():
    provider = ScriptedProvider(["this is not json"])
    domain = await classify_domain(provider, "A ball is thrown as a projectile")
    assert domain == "mechanics"


def test_parse_json_handles_fences():
    data = parse_json('```json\n{"a": 1, "b": "x"}\n```')
    assert data == {"a": 1, "b": "x"}


def test_coerce_float_variants():
    assert coerce_float("20 m/s") == 20.0
    assert coerce_float("1,000") == 1000.0
    assert coerce_float(5) == 5.0
    assert coerce_float(None) is None
    assert coerce_float(True) is None
