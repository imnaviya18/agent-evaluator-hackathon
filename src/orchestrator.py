"""
Orchestrator: coordinates the full test pipeline.
Generates scenarios/attacks, runs them against the agent (sandbox),
classifies failures/security, calculates scorecards, and saves results.
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

from scenario_generator import generate_scenarios
from attack_generator import generate_attacks
from failure_classifier import classify_batch as classify_failures
from security_classifier import classify_batch as classify_security, calculate_security_score
import storage

# --- Make the repo-root-level `sandbox` package importable regardless of
# how this module is launched (e.g. `uvicorn main:app --app-dir src`,
# which only puts `src` on sys.path by default). ---
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sandbox.sandbox_runner import SandboxRunner, Agent  # noqa: E402
from sandbox.security_monitor import SecurityMonitor  # noqa: E402

# --- Config for cost savings estimate ---
MANUAL_MINUTES_PER_SCENARIO = 5  # rough estimate: manual QA time per test case
HOURLY_RATE_USD = 40  # rough estimate: QA engineer hourly rate

# --- Config for sandbox execution ---
SANDBOX_MAX_STEPS = 10
SANDBOX_TIMEOUT_SECONDS = 30


def _run_sandbox(
    runner: SandboxRunner,
    agent: Agent,
    monitor: SecurityMonitor,
    input_text: str,
) -> dict:
    """
    Runs a single input against Member 2's Sandbox Runner and returns
    a normalized result for the rest of the pipeline.

    NOTE: `agent` here is Member 2's local demo Agent (sandbox/sandbox_runner.py),
    which is a hardcoded travel-booking agent (it parses flight/hotel-style
    tasks out of the input text via regex) -- it does not dynamically build
    an agent from `agent_description`. `agent_description` is still used
    for reporting/labeling, but the sandbox always exercises the same demo
    agent regardless of what the user described. If a real pluggable-agent
    interface is added later, only this function needs to change.
    """
    scenario = {
        "name": "generated_case",
        "description": agent.description,
        "task": input_text,
    }

    trace = runner.run_scenario(
        agent,
        scenario,
        max_steps=SANDBOX_MAX_STEPS,
        timeout_seconds=SANDBOX_TIMEOUT_SECONDS,
    )
    trace_dict = trace.to_dict()

    security_audit = monitor.audit_trace(trace_dict)

    return {
        "response": trace_dict["final_output"],
        "traces": trace_dict["tool_traces"],
        "safety_issues": security_audit["issues"],
        "timed_out": trace_dict["failure_detected"] == "timeout",
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

    # Sandbox setup: one runner + one demo agent + one security monitor per
    # test run, shared across every scenario/attack in this run. Tool state
    # is reset internally before each scenario by SandboxRunner.run_scenario.
    sandbox_runner = SandboxRunner(auto_persist=False)
    sandbox_agent = Agent(
        name="evaluated_agent",
        description=agent_description,
        tools=sandbox_runner.tools,
    )
    security_monitor = SecurityMonitor(allowed_tools=tools or None)

    # 1. Generate scenarios (returns dict keyed by category: normal/edge/adversarial/pressure)
    scenario_categories = generate_scenarios(agent_description, tools, model=model)
    all_scenarios = [s for scenarios in scenario_categories.values() for s in scenarios]

    # 2. Generate attacks
    attacks = generate_attacks(agent_description, model=model)

    # 3. Run each scenario against the sandbox
    scenario_runs = []
    for s in all_scenarios:
        sandbox_result = _run_sandbox(sandbox_runner, sandbox_agent, security_monitor, s["input"])
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
        sandbox_result = _run_sandbox(sandbox_runner, sandbox_agent, security_monitor, a["input"])
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