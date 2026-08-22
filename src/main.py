"""
FastAPI app for the agent-evaluator: local-only, no auth, CORS enabled.
Run with: uvicorn main:app --reload --port 8000 --app-dir src
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import TestRequest, TestResponse
from orchestrator import run_full_test
import storage

app = FastAPI(title="Agent Evaluator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/test", response_model=TestResponse)
def run_test(request: TestRequest):
    try:
        result = run_full_test(
            agent_description=request.agent_description,
            tools=request.tools,
            model=request.model,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{test_id}")
def get_results(test_id: str):
    result = storage.load_results(test_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No results found for test_id '{test_id}'")
    return result


@app.get("/api/history")
def get_history():
    return storage.get_history()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Agent Evaluator API is running"}