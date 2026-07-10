# Deployment & Scaling

The system deploys as two separated services. The current live architecture uses **Vercel** for
the Next.js frontend and **Render** for the Python FastAPI backend.

> Live instance: [https://elliott-wave-web.vercel.app](https://elliott-wave-web.vercel.app)

## Contents

- [Frontend (Vercel)](#frontend-vercel)
- [Backend (Render / Docker)](#backend-render--docker)
- [Scaling notes](#scaling-notes)
- [Security checklist](#security-checklist)

## Frontend (Vercel)

- **Framework preset:** Next.js
- **Root directory:** `apps/web` — critical: must be set before deploying
- **Environment variables:**
  - `NEXT_PUBLIC_API_URL` = `https://<your-render-api-url>.onrender.com`

## Backend (Render / Docker)

Deploy the repository root (`.`) as a Docker Web Service, pointing to `apps/api/Dockerfile`.

- **Environment variables:**
  - `EWL_ENV=production` — enforces CORS configuration and hides OpenAPI docs
  - `EWL_API_CORS_ORIGINS=https://<your-vercel-frontend-url>.vercel.app`
  - `EWL_CACHE_DIR=/app/data/.cache` — points the caching engine at the writable volume in the
    Docker container
  - `OLLAMA_API_KEY=<your key>`

The API fails fast at startup if `EWL_ENV=production` is set without a CORS allowlist — the
permissive dev regex must never serve production traffic.

> [!WARNING]
> **Do not set `ANALYST_QA=1` on this image.** [`apps/api/Dockerfile`](../apps/api/Dockerfile)
> installs `--extra api` only, so `sentence-transformers` is absent and **Ask** cannot run. The
> service detects the missing extra at build time and disables the embedder, so `/api/v1/qa`
> answers `503` and `/api/ready` reports `qa_enabled: false` — but the flag is still a lie about
> intent. To actually serve Ask, add `--extra grounding` to both `uv sync` lines in the Dockerfile
> and give the instance enough memory for torch plus the 768-dim embedding model (~440MB of wheels
> and well over Render's free-tier 512MB RAM).

## Scaling notes

> [!IMPORTANT]
> **Run one worker per process.** In-process caches (price parquet cache, LLM response cache,
> wave-count memoization) aren't shared across workers, so `uvicorn --workers N` causes
> cross-worker cache misses. To scale horizontally, use a sticky-routing reverse proxy or move
> the caches to Redis.

Other cost/latency characteristics worth knowing:

- LLM narrations are cached on disk with content-derived keys, so repeat views of the same
  scenario are free and stream instantly (the UI shows cached playback without a fake typewriter).
- Price data has per-timeframe TTLs (day 12h / week 1d / month 3d), so yfinance is only hit when
  a bar could actually have changed.

## Security checklist

> [!WARNING]
> Endpoints have **no app-level auth and no rate limiting** — the live deployment relies on CORS,
> the force-refresh guard, and caching to bound cost. For anything beyond a demo:

- Set `EWL_API_CORS_ORIGINS` to the exact frontend origin(s).
- Set `EWL_DISABLE_FORCE_REFRESH=1` to block the cache bypass that lets clients burn unbounded
  LLM calls.
- Keep `EWL_ENV=production` so OpenAPI docs stay hidden and misconfigured CORS fails at startup.
- Put a rate limiter (or an auth proxy) in front of the API before exposing it beyond a portfolio
  demo audience.
