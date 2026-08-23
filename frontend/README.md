# Sentinel — Agent Evaluator Console

A responsive React/Vite frontend for the active FastAPI agent-evaluator backend in the parent repository. The interface follows the supplied visual reference: black surfaces, high-contrast ivory typography, hard red accents, mono labels, grid textures, and a data-console feel.

## Run locally

From this directory:

```bash
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000` for the backend API. Start the active backend from the repository root with:

```bash
uv run uvicorn main:app --reload --port 8000 --app-dir src
```

If the API is hosted elsewhere, set `VITE_API_BASE_URL` before starting Vite or use **Connection** in the top-right of the console. The backend already allows CORS for local development.

## Connected endpoints

| Backend endpoint | Frontend behavior |
| --- | --- |
| `GET /api/health` | Live API status indicator in the top bar |
| `POST /api/test` | Test Lab form submits `agent_description`, `tools`, and `model`, then renders the complete scorecard |
| `GET /api/history` | Overview activity feed and Run History table |
| `GET /api/results/{test_id}` | Full scenario/attack drill-down for a selected persisted run |

The frontend consumes the response contract defined in `src/models.py`. It renders scenario failure taxonomy, severity, recommendations, attack classifications, pass/security scorecards, cost savings, runtime, source metadata, and raw JSON export.

## Backend note

The repository contains a legacy Flask/Peewee scaffold under `app/` and `run.py`, but the completed agent-evaluator functionality is the FastAPI service under `src/`. This frontend targets the active FastAPI routes and intentionally does not target the empty legacy Flask route registry.

## PRD coverage audit

The console now covers the frontend-visible portions of the PRD: agent description, task domain context, available tools, model selection, scenario and attack execution, failure taxonomy, scorecard visualization, cost-savings readout, persisted run history, version-over-version regression comparison, deterioration alerting, expandable findings, and JSON export.

The active backend does not currently expose separate APIs for raw generated scenarios, deterministic replay, sandbox traces, API-key management, agent-version identifiers, or a dedicated regression endpoint. The frontend therefore renders the classified scenario/attack arrays returned by `POST /api/test` and compares persisted history summaries locally. It also reports the backend's Ollama prerequisite in the Test Lab instead of presenting a non-functional model management control.
