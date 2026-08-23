"""
Sandbox package public API for local-first agent evaluation.
"""

from .sandbox_runner import SandboxRunner, Agent
from .mock_tools import MockTools
from .trace_storage import TraceStorage
from .enhanced_guardrails import EnhancedGuardrails
from .security_monitor import SecurityMonitor
from .replay_harness import ReplayHarness

__all__ = [
    "SandboxRunner",
    "Agent",
    "MockTools",
    "TraceStorage",
    "EnhancedGuardrails",
    "SecurityMonitor",
    "ReplayHarness",
    "run_tests",
]


def run_tests(
    agent_name: str,
    agent_description: str,
    scenarios: list,
    max_steps: int = 10,
    timeout_seconds: int = 30,
):
    """
    Main evaluation entry point.

    Executes an agent against a list of scenarios offline in a secure mock sandbox.
    Zero external network calls, zero data leaves the machine.
    """
    tools = MockTools()
    agent = Agent(agent_name, agent_description, tools)
    storage = TraceStorage()
    runner = SandboxRunner(tools=tools, storage=storage, auto_persist=True)
    traces = runner.run_batch(
        agent,
        scenarios,
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
    )
    storage.save_batch_traces([t.to_dict() for t in traces])
    return {
        "traces": [t.to_dict() for t in traces],
        "statistics": runner.get_statistics(),
    }
