"""
Orchestrator: coordinates the full test pipeline.
Generates scenarios/attacks, runs them against the agent (sandbox),
classifies failures/security, calculates scorecards, and saves results.
"""

import uuid
from datetime import datetime

from scenario_generator import generate_scenarios
from attack_generator import generate_attacks
from failure_classifier import classify_batch as classify_failures
from security_classifier import classify_batch as classify_security, calculate_security_score
import storage

# --- Config for cost savings estimate ---
MANUAL_MINUTES_PER_SCENARIO = 5  # rough estimate: manual QA time per test case
HOURLY_RATE_USD = 40  # rough estimate: QA engineer hourly rate


def _run_sandbox(agent_description: str, input_text: str) -> dict:
    """
    PLACEHOLDER for Member 2's sandbox integration.
    Should call the actual agent and return its response + tool traces.
    Replace this function's body once the real sandbox API/module is ready.
    """
    return {
        "response": f"[STUB RESPONSE] Agent would respond to: '{input_text}'",
        "traces": [],
        "safety_issues": [],
        "timed_out": False,
    }


def _build_scorecard(failure_results: list[dict]) -> dict:
    total = len(failure_results)
    passed = sum(1 for r in failure_results if r["failure_type"] == "PASS")
    failed = total - passed

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in failure_results:
        sev = r.get("severity")
        if sev in severity_counts:
            severity_counts[sev] += 1

    return {
        "total_scenarios": total,
        "passed": passed,
        "failed": failed,
        "critical_failures": severity_counts["CRITICAL"],
        "high_failures": severity_counts["HIGH"],
        "medium_failures": severity_counts["MEDIUM"],
        "low_failures": severity_counts["LOW"],
        "pass_rate": round((passed / total * 100) if total else 0.0, 2),
    }


def _build_security_scorecard(security_results: list[dict]) -> dict:
    total = len(security_results)
    passed = sum(1 for r in security_results if r["classification"] == "PASS")
    partial = sum(1 for r in security_results if r["classification"] == "PARTIAL")
    failed = sum(1 for r in security_results if r["classification"] == "FAIL")
    score = calculate_security_score(security_results)

    return {
        "total_attacks": total,
        "passed": passed,
        "partial": partial,
        "failed": failed,
        "security_score": score,
    }


def _calculate_cost_savings(num_scenarios: int, num_attacks: int, runtime_seconds: float) -> dict:
    total_cases = num_scenarios + num_attacks
    manual_hours = (total_cases * MANUAL_MINUTES_PER_SCENARIO) / 60
    manual_cost = manual_hours * HOURLY_RATE_USD
    automated_minutes = runtime_seconds / 60
    automated_cost = (automated_minutes / 60) * HOURLY_RATE_USD  # negligible, but kept for completeness

    return {
        "estimated_manual_hours": round(manual_hours, 2),
        "estimated_manual_cost_usd": round(manual_cost, 2),
        "automated_runtime_minutes": round(automated_minutes, 2),
        "estimated_savings_usd": round(manual_cost - automated_cost, 2),
    }


def run_full_test(agent_description: str, tools: list[str], model: str = "llama3.1:8b") -> dict:
    """
    Runs the complete pipeline:
    1. Generate scenarios
    2. Generate attacks
    3. Run each against the sandbox (stubbed for now)
    4. Classify failures
    5. Classify security
    6. Calculate scorecards + cost savings
    7. Save everything
    """
    start_time = datetime.now()
    test_id = str(uuid.uuid4())[:8]

    # 1. Generate scenarios (returns dict keyed by category: normal/edge/adversarial/pressure)
    scenario_categories = generate_scenarios(agent_description, tools, model=model)
    all_scenarios = [s for scenarios in scenario_categories.values() for s in scenarios]

    # 2. Generate attacks
    attacks = generate_attacks(agent_description, model=model)

    # 3. Run each scenario against the sandbox
    scenario_runs = []
    for s in all_scenarios:
        sandbox_result = _run_sandbox(agent_description, s["input"])
        scenario_runs.append({
            "scenario_id": s["id"],
            "input": s["input"],
            "output": sandbox_result["response"],
            "traces": sandbox_result["traces"],
            "safety_issues": sandbox_result["safety_issues"],
            "timed_out": sandbox_result["timed_out"],
        })

    # 3b. Run each attack against the sandbox
    attack_runs = []
    for a in attacks:
        sandbox_result = _run_sandbox(agent_description, a["input"])
        attack_runs.append({
            "attack_id": a["id"],
            "attack_type": a["type"],
            "attack": a["input"],
            "response": sandbox_result["response"],
            "traces": sandbox_result["traces"],
            "safety_issues": sandbox_result["safety_issues"],
        })

    # 4. Classify failures
    failure_results = classify_failures(scenario_runs, model=model)

    # 5. Classify security
    security_results = classify_security(attack_runs, model=model)

    # 6. Scorecards + cost savings
    scorecard = _build_scorecard(failure_results)
    security_scorecard = _build_security_scorecard(security_results)
    runtime_seconds = (datetime.now() - start_time).total_seconds()
    cost_savings = _calculate_cost_savings(len(all_scenarios), len(attacks), runtime_seconds)

    result = {
        "test_id": test_id,
        "timestamp": start_time.isoformat(),
        "agent_description": agent_description,
        "scenario_results": failure_results,
        "attack_results": security_results,
        "scorecard": scorecard,
        "security_scorecard": security_scorecard,
        "cost_savings": cost_savings,
    }

    # 7. Save
    storage.save_results(result, test_id)

    return result