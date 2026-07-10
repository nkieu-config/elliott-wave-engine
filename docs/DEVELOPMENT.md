# Development Guide

Everything you need to run, use, and test the project locally.

> For the one-command Docker path, see [Quick Start in the README](../README.md#quick-start).
> For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [Using the dashboard](#using-the-dashboard)
- [Testing](#testing)
- [Environment variables](#environment-variables)
- [Directory tree](#directory-tree)

## Prerequisites

| Software                 | Version      | Notes                                                                                                      |
| ------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------- |
| **Python**               | ≥ 3.11       | uv manages the version and environment for you                                                             |
| **uv**                   | ≥ 0.4        | Python package manager — see the [install guide](https://docs.astral.sh/uv/getting-started/installation/)  |
| **Node.js**              | ≥ 20         | Developed on v22; ships with npm (`package.json` engines pin ≥ 20)                                         |
| **Internet**             | Required     | For yfinance price data + Ollama Cloud                                                                     |
| **Ollama Cloud API key** | _(optional)_ | Needed only for the AI Analyst — [get a key](https://ollama.com/settings/keys)                             |

> [!NOTE]
> Without an Ollama Cloud API key the chart / KPI / scoring features work normally — only
> **AI Reading** and **Ask** need an LLM (or a local [Ollama](https://ollama.com) running the
> fallback model, to which the analyst fails over automatically). **Ask** also needs
> `ANALYST_QA=1` plus the `grounding` extra — see [Environment variables](#environment-variables).

## Installation

```bash
# 1) Clone the project
git clone https://github.com/nkieu-config/elliott-wave-ai-project.git
cd elliott-wave-ai-project

# 2) Install Python dependencies (uv creates .venv and installs from uv.lock)
uv sync --extra api

# 3) Install frontend dependencies
cd apps/web
npm install
cd ../..
```

## Configuration

```bash
# Copy the example file, then fill in your values
cp .env.example .env
```

Edit `.env` and add your Ollama Cloud API key:

```
OLLAMA_API_KEY=<your key from https://ollama.com/settings/keys>
```

The frontend calls `http://localhost:8000` by default, so no extra setup is needed for local
development. To point it at a different API, create `apps/web/.env.local` (git-ignored):

```
NEXT_PUBLIC_API_URL=https://your-api-host
```

## Running

Open two terminals:

```bash
# Terminal 1 — Backend (port 8000)
uv run uvicorn apps.api.main:app --reload --port 8000
```

```bash
# Terminal 2 — Frontend (port 3000)
cd apps/web
npm run dev
```

Then open your browser:

- **Dashboard:** http://localhost:3000
- **API docs (Swagger UI):** http://localhost:8000/docs

## Using the dashboard

1. Open http://localhost:3000 — the app loads a default view (symbol `DDOG`, weekly, max range).
   The first load fetches live data from yfinance and caches it under `data/` automatically;
   subsequent loads read from the cache and appear instantly.
2. Choose a **symbol / period / timeframe** to fetch and re-analyze. Any symbol not yet cached is
   fetched live from yfinance.
3. The system ranks **wave-counting hypotheses (scenarios)** by a confidence score; inspect them
   one at a time and open a scenario to see its **score breakdown** (where the confidence comes
   from).
4. Toggle display layers (raw / trendline / latest) on the chart, then read the **AI Reading**
   panel, which streams a narration in real time (with theory citations) across four lenses:
   - **Structure** — what the current count is
   - **Outlook** — targets and the conditions that confirm them
   - **Risk** — the weakest link / invalidation
   - **Alternative** — the runner-up scenarios if this count is wrong
5. Press **`/`** or click **Ask** in the AI Reading header to ask a free-form Elliott Wave theory
   question — answered from the theory corpus with citations, optionally grounded in the selected
   scenario (requires `ANALYST_QA=1`).

## Testing

```bash
# Python
uv sync --extra api --extra dev   # install the test toolchain (first time only)
uv run pytest -m "not slow"       # fast tests
uv run pytest                     # full suite

# Frontend
cd apps/web
npm test
```

CI runs the same checks on every push/PR — `ruff` + `pytest` (branch coverage ≥ 75%) on a
Python 3.11 + 3.12 matrix, and `tsc` + `eslint` + `next build` + `vitest` — see
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Environment variables

| Variable                    | Scope   | Default                 | Description                                                                                                          |
| --------------------------- | ------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `OLLAMA_API_KEY`            | analyst | _(required for AI)_     | Ollama Cloud API key                                                                                                 |
| `OLLAMA_PRIMARY_MODEL`      | analyst | `qwen3-next:80b-cloud`  | Primary model (cloud)                                                                                                |
| `OLLAMA_FALLBACK_MODEL`     | analyst | `qwen3.5:9b`            | Fallback model (local Ollama), used if the cloud call fails                                                          |
| `ANALYST_QA`                | analyst | _(off)_                 | Set to `1` to enable the **Ask** theory Q&A (embedding retrieval; requires `uv sync --extra api --extra grounding`)  |
| `ANALYST_GROUNDING_CHECK`   | analyst | _(off)_                 | Set to `1` to enable the semantic grounding check (requires the `grounding` extra, pulls ~440MB torch)               |
| `EWL_API_CORS_ORIGINS`      | api     | _(dev regex)_           | Comma-separated allowlist of origins for production                                                                  |
| `EWL_ENV`                   | api     | _(unset)_               | Set to `production` to enforce CORS configuration and hide OpenAPI docs                                              |
| `EWL_DISABLE_FORCE_REFRESH` | api     | _(off)_                 | Set to `1` to disable force-refresh (prevents cache bypass that burns LLM calls on public deploys)                   |
| `EWL_CACHE_DIR`             | engine  | `<repo>/data`           | Directory for the price parquet cache                                                                                |
| `EWL_CACHE_MAX_BYTES`       | engine  | `268435456` (256MB)     | LRU budget for the parquet cache; over budget evicts oldest-fetched files first; `0` disables eviction               |
| `NEXT_PUBLIC_API_URL`       | web     | `http://localhost:8000` | API address the frontend calls                                                                                       |

Normally only `OLLAMA_API_KEY` (and `EWL_API_CORS_ORIGINS` when deploying) need setting; the rest
have working defaults. Finer knobs — Ollama timeouts / retries / concurrency, logging, Sentry
DSNs — also read from the environment; see
[`ollama_client.py`](../infra/llm/ollama_client.py),
[`logging_config.py`](../engine/logging_config.py), and `apps/web/sentry.*.config.ts`.

## Directory tree

```
elliott-wave-ai-project/
├── README.md                     # Project overview (start here)
├── pyproject.toml                # Python package definition + dependencies (managed by uv)
├── uv.lock                       # Pinned dependency versions for reproducible installs
├── .env.example                  # Example configuration (copy to .env and fill in)
├── docker-compose.yml            # One-command full-stack run (api + web)
│
├── engine/                       # ── Symbolic core: rule-based Elliott Wave counter ──
│   ├── pivot.py                  #    Pivot detection (ATR-based ZigZag pivots)
│   ├── anchor.py                 #    Wave start selection (anchor)
│   ├── adaptive.py               #    Wave pattern families (3-wave / 5-wave trend / sideway)
│   ├── pipeline.py               #    Orchestration: pivots → anchor → wave counting
│   ├── parser/                   #    Beam-search wave counter + scoring
│   ├── verifiers/                #    Wave-rule checkers (trend / sideway / 3-wave / link)
│   ├── degree/                   #    Wave degree labeling (hierarchy)
│   └── data/                     #    BarSource / BarCache ports + repository (no vendor code)
│
├── analyst/                      # ── Neuro core: LLM-powered analyst ──
│   ├── orchestrator.py           #    Main coordinator (Analyst) + default singleton factory
│   ├── diagnostics/              #    Deterministic Layer-1: targets / bottlenecks / confirmation / decision / succession
│   ├── client/                   #    LLMClient port + response cache + grounding gate
│   ├── theory/                   #    Theory retrieval (RAG): chunker / embedder / retriever from docs/
│   ├── prompts/                  #    Prompt templates: 4 narration modes + theory Q&A + repair
│   └── schemas/ , serialization/ #    Result schemas + LLM input serialization
│
├── infra/                        # ── Adapters: the only code that talks to the outside world ──
│   ├── llm/                      #    OllamaClient — cloud primary + local failover
│   └── market_data/              #    YFinanceSource + ParquetCache (pandas confined here)
│
├── apps/
│   ├── api/                      # Backend: FastAPI — routers/ (pipeline, analyst, qa, health),
│   │                             #          services/, schemas.py, serializers.py, pipeline_ops.py
│   │                             #          + Dockerfile (image built from repo root)
│   └── web/                      # Frontend: Next.js 15 + React 19 (app/, components/, lib/)
│                                 #          + Dockerfile (multi-stage standalone build)
│
├── data/                         # Price cache (.parquet) — created automatically from yfinance
├── docs/                         # Project docs + Elliott Wave theory corpus (RAG source)
└── tests/                        # pytest suite (engine / analyst / infra / apps)
```
