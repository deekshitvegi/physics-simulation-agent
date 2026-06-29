"""API tests via Starlette's TestClient (no real network/LLM)."""
import pytest
from fastapi.testclient import TestClient

import main
from providers import LLMProvider

client = TestClient(main.app)


class ScriptedProvider(LLMProvider):
    name = "scripted"

    def __init__(self, responses):
        super().__init__("dummy-key", "scripted")
        self._responses = list(responses)

    async def _generate(self, system: str, user: str) -> str:
        return self._responses.pop(0)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_lists_endpoints():
    r = client.get("/")
    assert r.status_code == 200
    assert "/api/solve" in r.json()["endpoints"]


def test_domains_returns_eight():
    r = client.get("/api/domains")
    assert r.status_code == 200
    data = r.json()
    assert len(data["domains"]) == 8
    assert "projectile" in data["simulations"]


def test_providers_shape():
    r = client.get("/api/providers")
    assert r.status_code == 200
    data = r.json()
    assert set(data["providers"]) == {"gemini", "groq", "mistral", "claude", "openai"}
    assert isinstance(data["available"], list)


def test_quick_solve_projectile():
    r = client.post(
        "/api/solve/quick",
        json={"equation_id": "projectile_range", "target": "R", "variables": {"v0": 20, "theta": 45}},
    )
    assert r.status_code == 200
    data = r.json()
    assert abs(data["answer"]["value"] - 40.8) < 0.5
    assert data["simulation_type"] == "projectile"


def test_quick_solve_missing_value_422():
    r = client.post(
        "/api/solve/quick",
        json={"equation_id": "wave_speed", "target": "v", "variables": {"f": 440}},
    )
    assert r.status_code == 422


def test_solve_unconfigured_provider_400():
    r = client.post(
        "/api/solve",
        json={"problem": "A ball is thrown at 45 degrees with 20 m/s", "provider": "gemini"},
    )
    assert r.status_code == 400  # no API key configured


def test_solve_full_pipeline(monkeypatch):
    def fake_create(name=None, settings=None):
        return ScriptedProvider([
            '{"domain": "mechanics"}',
            '{"equation_id": "projectile_range", "target": "R", "knowns": {"v0": 20, "theta": 45}}',
            "It travels about 40.8 m.",
        ])

    monkeypatch.setattr(main.ProviderFactory, "create", staticmethod(fake_create))
    r = client.post("/api/solve", json={"problem": "A ball thrown at 45 deg, 20 m/s, range?"})
    assert r.status_code == 200
    data = r.json()
    assert data["domain"] == "mechanics"
    assert abs(data["answer"]["value"] - 40.8) < 0.5
    assert data["simulation_type"] == "projectile"
    assert data["explanation"]


def test_solve_empty_problem_422():
    r = client.post("/api/solve", json={"problem": ""})
    assert r.status_code == 422  # pydantic min_length validation
