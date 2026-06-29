# Physics Simulation Agent

An AI agent that solves physics and math word problems in plain English and renders
**live, interactive simulations** you can manipulate in real time. Answers are computed
**symbolically with SymPy** — never hallucinated by the LLM.

> Status: 🚧 Under active construction. See [Build Progress](#build-progress).

## Features

- Natural-language problem input
- **Model-agnostic** LLM support: Gemini, Llama (Groq), Mistral, Claude, OpenAI — swap with one env var
- Symbolic math solving via **SymPy** — no hallucinated answers
- Live interactive simulations: projectile, pendulum, wave, circuit, orbital, collision
- Real-time variable sliders — tweak inputs and watch the simulation update
- 8 physics domains: mechanics, waves, electricity, thermodynamics, gravitation, fluids, quantum, relativity

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python + FastAPI |
| LLM layer | Model-agnostic provider system (Gemini / Groq / Mistral / Claude / OpenAI) |
| Math engine | SymPy (symbolic, exact) |
| Frontend | React + TypeScript + Tailwind CSS |
| Simulations | p5.js |
| Deploy | Docker + docker-compose, Vercel (frontend), GitHub Actions (CI/CD) |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- At least one LLM API key (Gemini free tier is the easiest to start with)

### Backend
```bash
cd backend
cp .env.example .env        # then fill in your API key(s)
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Docker (full stack)
```bash
cp backend/.env.example backend/.env   # fill in API keys
docker-compose up --build
```

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | Active provider: `gemini` / `groq` / `mistral` / `claude` / `openai` |
| `GEMINI_API_KEY` | Google AI Studio key |
| `GROQ_API_KEY` | Groq API key (runs Llama 3.3-70b) |
| `MISTRAL_API_KEY` | Mistral API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `PORT` | Server port (default 8000) |

### Frontend
| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Base URL of the backend API |

## Supported Physics Domains

- **Mechanics** — projectile, Newton's laws, collisions, rotation, circular motion
- **Waves & Optics** — interference, refraction, Snell's law, resonance
- **Electricity & Circuits** — Ohm's law, series/parallel, RC/RL, power
- **Thermodynamics** — ideal gas, heat transfer, Carnot
- **Gravitation** — orbital mechanics, escape velocity, gravitational force
- **Fluid Dynamics** — Bernoulli, continuity, buoyancy
- **Quantum Basics** — energy levels, photoelectric effect, de Broglie wavelength
- **Relativity Basics** — time dilation, length contraction, mass-energy

## Example Problems

- "A ball is thrown at 45° with 20 m/s. How far does it travel?"
- "A pendulum is 2 meters long. What is its period?"
- "Two resistors of 4Ω and 6Ω in parallel. Total resistance?"
- "A wave has frequency 440 Hz and wavelength 0.78 m. What is its speed?"
- "An ideal gas at 300 K occupies 2 L at 1 atm. What volume at 600 K and 2 atm?"
- "What is the escape velocity from Earth?"

## Architecture

```
User problem (plain English)
        │
        ▼
┌──────────────────────────────────────────────┐
│  Physics Agent Pipeline (backend)            │
│  1. Classify domain          (LLM)           │
│  2. Extract variables        (LLM)           │
│  3. Select equations         (LLM + library) │
│  4. Solve symbolically       (SymPy — exact) │
│  5. Map to simulation        (deterministic) │
│  6. Explain step-by-step     (LLM)           │
└──────────────────────────────────────────────┘
        │
        ▼
  JSON: answer + steps + simulation_type + params
        │
        ▼
  React UI: KaTeX solution  +  live p5.js simulation  +  sliders
```

The LLM layer is fully model-agnostic: every provider implements a single
`LLMProvider.complete(system, user)` interface, and a `ProviderFactory` selects
the active one from `LLM_PROVIDER`. Core agent/solver logic never references a
specific provider.

## Build Progress

- [x] Project structure & gitignore
- [ ] Model-agnostic LLM provider system
- [ ] SymPy solver & equation library
- [ ] Physics agent pipeline
- [ ] FastAPI routes & CORS
- [ ] React frontend scaffold
- [ ] Simulations (projectile, pendulum, wave, circuit, orbital, collision)
- [ ] Variable sliders
- [ ] Docker & docker-compose
- [ ] GitHub Actions CI/CD

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
