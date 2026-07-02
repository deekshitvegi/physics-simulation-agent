# Physics Tutor Agent

An AI agent that **tutors physics and math by conversation** — but does the actual
**math with a deterministic engine (SymPy), not by guessing**. It can search the
web to find published solutions, render live interactive simulations, read problem
images, and it is **honest about how confident each answer is**.

![CI](https://github.com/deekshitvegi/physics-simulation-agent/actions/workflows/ci.yml/badge.svg)

> **Core principle: _LLM for language, SymPy for truth._** The language model
> understands the problem, explains it, and orchestrates tools — but every number
> is computed by a computer algebra system, so answers are never hallucinated.

---

## What makes it different — the honesty model

Most AI tutors confidently state answers whether or not they're right. This one
**labels every answer** so you know what to trust:

| Badge | Meaning |
|-------|---------|
| 🟢 **Computed exactly with SymPy** | The number came from the math engine — trust it. |
| 🔵 **Based on web sources** | Found in a published solution — links shown so you can verify. |
| 🟡 **Conceptual reasoning — not verified** | The model's reasoning, no computation — be skeptical. |

It is also told to **refuse to bluff** — to say *"I can't solve this reliably"*
rather than invent a confident wrong answer.

## Features

- **Conversational tutor** with tool-calling and multi-turn memory
- **Exact symbolic math** — `calculate` and `solve_equation` run SymPy
- **62-formula vetted library** across 8 domains, exposed as a `solve_with_formula`
  tool so the agent uses correct-by-construction physics
- **Web research (RAG)** — searches the *exact* question, reads the solution
  page/PDF, and **cites its sources**. If your numbers differ from a found
  solution, it re-applies the method to *your* values with SymPy.
- **Vision** — attach a problem screenshot/diagram (Groq Llama-4 Scout)
- **6 live p5.js simulations** — projectile, pendulum, wave, circuit, orbital, collision
- **Model-agnostic** — Gemini, Groq (Llama), Mistral, Claude, or OpenAI via one env var

## How the agent works

```
You ask a question (text or image)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  Tutor agent (LLM) — understands + explains + orchestrates │
│     │  picks tools as needed                               │
│     ├── calculate / solve_equation   → exact SymPy math    │
│     ├── solve_with_formula           → vetted library      │
│     ├── search_web / fetch_url       → find & read solutions│
│     └── show_simulation              → live p5.js sim       │
└──────────────────────────────────────────────────────────┘
        │
        ▼
  Answer + worked steps + trust badge + sources + simulation
```

The LLM never does arithmetic. It decides *what* to compute and *which* formula
or source to use; the tools return exact results.

## Honest limitations (read this)

This is a real engineering project, so here's the truth about what it can't do:

- **Conceptual reasoning is capped by the model.** Hard, novel, conceptual
  problems (e.g. JEE-Advanced "which options are true" with no computation) are
  only as good as the underlying model. On the **free Groq/Llama tier** these are
  unreliable — it can be wrong and can be swayed by pushback.
- **Web research is powerful but imperfect.** It reliably solves *known/past-paper*
  problems when search lands on a real solution (verified: it answered a JEE
  Advanced 2017 MCQ correctly by reading the official paper) — but it can miss, and
  **reading full pages/PDFs burns tokens fast** (the free Groq tier has a daily
  token cap).
- **It is not a guaranteed answer key.** It's a tutor + research assistant that is
  *honest about its confidence*, not an oracle.

**The single biggest upgrade is a stronger model** — and because the provider
layer is model-agnostic, that's a **one-line `.env` change** (no code changes),
e.g. `LLM_PROVIDER=openai`. To escape the free-API **daily token cap** entirely,
run a model locally & unlimited with `LLM_PROVIDER=ollama` (weaker than a 70B, but
no limits and fully private).

## Quick Start

### Prerequisites
- Python 3.11+, Node.js 20+
- At least one LLM API key. **Groq** is free and fast (`console.groq.com/keys`).

### Backend
```bash
cd backend
cp .env.example .env        # then add your key, e.g. GROQ_API_KEY + LLM_PROVIDER=groq
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev                 # http://localhost:5173
```

### Docker (full stack)
```bash
cp backend/.env.example backend/.env   # add your API key
docker-compose up --build              # frontend on :5173, backend on :8000
```

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | Active provider: `gemini` / `groq` / `mistral` / `claude` / `openai` / `ollama` |
| `GROQ_API_KEY` | Groq key (free; runs Llama 3.3-70b for chat, Llama-4 Scout for vision) |
| `GEMINI_API_KEY` / `MISTRAL_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Other providers |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | Run a model **locally & unlimited** via [Ollama](https://ollama.com) — no key, no token cap (set `LLM_PROVIDER=ollama`) |
| `PORT` | Server port (default 8000) |
| `CORS_ORIGINS` | Comma-separated extra allowed origins (optional) |

### Frontend (`frontend/.env`)
| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend base URL (default `http://localhost:8000`) |

## API

| Endpoint | Purpose |
|----------|---------|
| `POST /api/chat` | Conversational tutor (tool-calling) — main endpoint |
| `POST /api/solve` | One-shot structured solve (classify → extract → SymPy → simulate) |
| `POST /api/solve/quick` | Re-solve with new variable values (no LLM) |
| `GET /api/providers` | Configured + available providers |
| `GET /api/domains` | Supported physics domains |
| `GET /health` | Health check |

## Tech Stack

- **Backend** — Python, FastAPI, SymPy, model-agnostic LLM layer, DuckDuckGo + BeautifulSoup/pypdf (web research)
- **Frontend** — React, TypeScript, Tailwind CSS, KaTeX, p5.js
- **Infra** — Docker + docker-compose, GitHub Actions CI, Vercel (frontend)

## Tests

```bash
cd backend && python -m pytest -q     # symbolic solver, agent pipeline, API
```

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file.
