"""
Tests for Sandbox Execution and run_tests API.
"""

from sandbox import run_tests, SandboxRunner, Agent, MockTools


def test_sandbox_run_tests_basic():
    scenarios = [
        {
            "name": "Flight Search Test",
            "task": "Find flights from New York to London for 2026-08-25.",
        }
    ]
    result = run_tests(
        agent_name="TestAgent",
        agent_description="Test Assistant",
        scenarios=scenarios,
        max_steps=5,
        timeout_seconds=10,
    )
    assert result is not None
    assert "traces" in result
    assert "statistics" in result
    assert len(result["traces"]) == 1
    assert result["statistics"]["total_tests"] == 1


def test_sandbox_runner_direct():
    tools = MockTools()
    agent = Agent("DirectAgent", "Test Agent", tools)
    runner = SandboxRunner(tools=tools, auto_persist=False)
    trace = runner.run_scenario(
        agent=agent,
        scenario={"name": "Hotel Scenario", "task": "Check hotels in Paris."},
        max_steps=5,
    )
    assert trace is not None
    assert trace.scenario_name == "Hotel Scenario"