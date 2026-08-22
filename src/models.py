"""
Pydantic models for the FastAPI app: request/response schemas
for test requests, results, and scorecards.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TestRequest(BaseModel):
    agent_description: str = Field(..., description="Description of the agent being tested")
    tools: list[str] = Field(default_factory=list, description="List of tools available to the agent")
    model: str = Field(default="llama3.1:8b", description="Ollama model to use for generation/classification")


class ScenarioResult(BaseModel):
    scenario_id: int
    input: str
    failure_type: str
    severity: str
    explanation: str
    recommendation: str
    source: str


class AttackResult(BaseModel):
    attack_id: int
    attack_type: str
    attack: str
    classification: str
    explanation: str
    source: str


class Scorecard(BaseModel):
    total_scenarios: int
    passed: int
    failed: int
    critical_failures: int
    high_failures: int
    medium_failures: int
    low_failures: int
    pass_rate: float


class SecurityScorecard(BaseModel):
    total_attacks: int
    passed: int
    partial: int
    failed: int
    security_score: float


class CostSavings(BaseModel):
    estimated_manual_hours: float
    estimated_manual_cost_usd: float
    automated_runtime_minutes: float
    estimated_savings_usd: float


class TestResponse(BaseModel):
    test_id: str
    timestamp: datetime
    agent_description: str
    scenario_results: list[ScenarioResult]
    attack_results: list[AttackResult]
    scorecard: Scorecard
    security_scorecard: SecurityScorecard
    cost_savings: CostSavings