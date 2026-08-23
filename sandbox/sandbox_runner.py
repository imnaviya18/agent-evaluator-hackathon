"""
SANDBOX RUNNER - Agent execution and evaluation orchestration.

Responsibilities:
- Execute an agent against one or many scenarios.
- Enforce max-step limits.
- Enforce execution timeouts.
- Reset mock-tool state between scenarios.
- Capture real tool results and traces.
- Detect loops, hallucination-like behavior, tool failures,
  timeouts, and execution exceptions.
- Persist completed execution traces through TraceStorage.
- Produce aggregate evaluation statistics.

Environment:
- Local only.
- No internet access.
- MockTools only.
"""

from __future__ import annotations

import copy
import re
import time
import uuid

from collections import Counter
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from .mock_tools import MockTools
    from .trace_storage import TraceStorage
except (ImportError, ValueError):
    from mock_tools import MockTools
    from trace_storage import TraceStorage


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class ToolCall:
    """Summary of an actual tool invocation."""

    tool_name: str
    params: Dict[str, Any]
    result: Any
    timestamp: str
    duration_ms: float
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "params": copy.deepcopy(self.params),
            "result": copy.deepcopy(self.result),
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class ExecutionTrace:
    """Complete record of one agent/scenario execution."""

    test_id: str
    agent_name: str
    agent_description: str

    scenario_name: str
    scenario_description: str
    scenario_task: str

    start_time: str
    end_time: str

    duration_seconds: float

    success: bool
    error_message: Optional[str] = None

    tool_calls: List[Dict[str, Any]] = field(
        default_factory=list
    )

    tool_traces: List[Dict[str, Any]] = field(
        default_factory=list
    )

    final_output: str = ""

    failure_detected: Optional[str] = None
    failure_details: Optional[Dict[str, Any]] = None

    security_events: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "agent_name": self.agent_name,
            "agent_description": self.agent_description,
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "scenario_task": self.scenario_task,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "tool_calls": copy.deepcopy(
                self.tool_calls
            ),
            "tool_traces": copy.deepcopy(
                self.tool_traces
            ),
            "final_output": self.final_output,
            "failure_detected": self.failure_detected,
            "failure_details": copy.deepcopy(
                self.failure_details
            ),
            "security_events": copy.deepcopy(
                self.security_events
            ),
            "metadata": copy.deepcopy(
                self.metadata
            ),
        }


# ============================================================
# AGENT INTERFACE
# ============================================================


class Agent:
    """
    Local test-agent implementation.

    In the final product this interface can be replaced/adapted
    to execute an uploaded real agent.

    The important contract is:
        execute(task, max_steps, timeout_seconds) -> dict
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: MockTools,
    ) -> None:
        self.name = name
        self.description = description
        self.tools = tools
        self.call_history: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # Internal helper
    # --------------------------------------------------------

    def _record_tool_result(
        self,
        tool_calls: List[Dict[str, Any]],
        before_trace_count: int,
    ) -> None:
        """
        Pull actual tool traces from MockTools and convert the
        newest call into the agent execution trace.
        """

        traces = self.tools.get_traces()

        if len(traces) <= before_trace_count:
            return

        latest = traces[-1]

        tool_calls.append(
            {
                "tool_name": latest.get(
                    "operation",
                    "unknown",
                ),
                "params": latest.get(
                    "arguments",
                    {},
                ),
                "result": latest.get(
                    "result"
                ),
                "timestamp": latest.get(
                    "timestamp"
                ),
                "duration_ms": latest.get(
                    "latency_ms",
                    0,
                ),
                "success": latest.get(
                    "success",
                    True,
                ),
                "error": latest.get(
                    "error"
                ),
                "trace_id": latest.get(
                    "trace_id"
                ),
            }
        )

    def _call(
        self,
        tool_calls: List[Dict[str, Any]],
        operation,
        max_steps: int,
    ) -> Any:
        """
        Execute one tool call while enforcing the step limit.
        """

        if len(tool_calls) >= max_steps:
            raise RuntimeError(
                f"Maximum step limit reached: {max_steps}"
            )

        before_trace_count = len(
            self.tools.get_traces()
        )

        result = operation()

        self._record_tool_result(
            tool_calls,
            before_trace_count,
        )

        return result

    # --------------------------------------------------------
    # Task parsing
    # --------------------------------------------------------

    @staticmethod
    def _extract_date(
        task: str,
        default: str = "2026-08-25",
    ) -> str:
        match = re.search(
            r"\b20\d{2}-\d{2}-\d{2}\b",
            task,
        )

        return (
            match.group(0)
            if match
            else default
        )

    @staticmethod
    def _extract_city_pair(
        task: str,
    ) -> tuple[str, str]:
        match = re.search(
            r"from\s+(.+?)\s+to\s+(.+?)(?:\s+on|\s+and|\s*$)",
            task,
            re.IGNORECASE,
        )

        if match:
            return (
                match.group(1).strip(),
                match.group(2).strip(),
            )

        return (
            "New York",
            "London",
        )

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    def execute(
        self,
        task: str,
        max_steps: int = 10,
        timeout_seconds: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute the local demonstration agent.

        Returns a structured result consumed by SandboxRunner.
        """

        if not isinstance(task, str):
            raise TypeError(
                "task must be a string."
            )

        if max_steps <= 0:
            raise ValueError(
                "max_steps must be greater than zero."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        start = time.perf_counter()

        tool_calls: List[
            Dict[str, Any]
        ] = []

        self.call_history = []

        origin, destination = (
            self._extract_city_pair(task)
        )

        flight_date = self._extract_date(
            task
        )

        try:
            # ------------------------------------------------
            # Flight search
            # ------------------------------------------------

            flights = self._call(
                tool_calls,
                lambda: self.tools.search_flights(
                    origin,
                    destination,
                    flight_date,
                ),
                max_steps,
            )

            self.call_history.extend(
                tool_calls
            )

            # ------------------------------------------------
            # Booking task
            # ------------------------------------------------

            wants_booking = any(
                keyword in task.lower()
                for keyword in (
                    "book",
                    "buy",
                    "reserve",
                )
            )

            if wants_booking:
                available = flights.get(
                    "flights",
                    []
                )

                if not available:
                    raise RuntimeError(
                        "Agent attempted to book a flight "
                        "but no matching flight was available."
                    )

                selected_flight = (
                    available[0]
                )

                self._call(
                    tool_calls,
                    lambda: self.tools.book_flight(
                        selected_flight[
                            "flight_id"
                        ],
                        "Test User",
                        "test@example.com",
                    ),
                    max_steps,
                )

            # ------------------------------------------------
            # Hotel task
            # ------------------------------------------------

            wants_hotel = any(
                keyword in task.lower()
                for keyword in (
                    "hotel",
                    "stay",
                )
            )

            if wants_hotel:
                self._call(
                    tool_calls,
                    lambda: self.tools.search_hotels(
                        destination,
                        "2026-08-26",
                        "2026-08-28",
                    ),
                    max_steps,
                )

            # ------------------------------------------------
            # Weather task
            # ------------------------------------------------

            if "weather" in task.lower():
                self._call(
                    tool_calls,
                    lambda: self.tools.get_weather(
                        destination
                    ),
                    max_steps,
                )

            # ------------------------------------------------
            # Loop simulation
            # ------------------------------------------------

            if (
                "loop" in task.lower()
                or "repeat" in task.lower()
                or "repeatedly" in task.lower()
            ):
                for _ in range(4):
                    self._call(
                        tool_calls,
                        lambda: self.tools.search_flights(
                            origin,
                            destination,
                            flight_date,
                        ),
                        max_steps,
                    )

            # ------------------------------------------------
            # Hallucination simulation
            # ------------------------------------------------

            if (
                "hallucinate"
                in task.lower()
                or "make up"
                in task.lower()
            ):
                self._call(
                    tool_calls,
                    lambda: self.tools.get_booking_details(
                        "FAKE123"
                    ),
                    max_steps,
                )

            duration = (
                time.perf_counter()
                - start
            )

            return {
                "success": True,
                "final_output": (
                    f"Successfully completed task: "
                    f"{task}"
                ),
                "tool_calls": tool_calls,
                "duration_seconds": duration,
                "error_message": None,
            }

        except Exception as exc:
            duration = (
                time.perf_counter()
                - start
            )

            return {
                "success": False,
                "final_output": "",
                "tool_calls": tool_calls,
                "duration_seconds": duration,
                "error_message": str(exc),
            }


# ============================================================
# SANDBOX RUNNER
# ============================================================


class SandboxRunner:
    """
    Executes agents in a local mock-tool sandbox.

    This class is responsible for orchestration, not security
    policy implementation. Dedicated security components can
    consume the traces generated here later.
    """

    def __init__(
        self,
        tools: Optional[MockTools] = None,
        storage: Optional[TraceStorage] = None,
        auto_persist: bool = True,
    ) -> None:
        self.tools = (
            tools
            if tools is not None
            else MockTools()
        )

        self.storage = (
            storage
            if storage is not None
            else TraceStorage()
        )

        self.auto_persist = auto_persist

        self.traces: List[
            ExecutionTrace
        ] = []

    # ========================================================
    # SINGLE SCENARIO
    # ========================================================

    def run_scenario(
        self,
        agent: Agent,
        scenario: Dict[str, Any],
        max_steps: int = 10,
        timeout_seconds: int = 30,
    ) -> ExecutionTrace:
        """
        Execute one scenario.

        Every scenario receives a clean tool state.
        """

        if not isinstance(
            scenario,
            dict,
        ):
            raise TypeError(
                "scenario must be a dictionary."
            )

        if max_steps <= 0:
            raise ValueError(
                "max_steps must be greater than zero."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        test_id = (
            f"TEST_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_"
            f"{uuid.uuid4().hex[:8].upper()}"
        )

        start_datetime = datetime.now(
            timezone.utc
        )

        trace = ExecutionTrace(
            test_id=test_id,
            agent_name=agent.name,
            agent_description=agent.description,
            scenario_name=scenario.get(
                "name",
                "Unknown Scenario",
            ),
            scenario_description=scenario.get(
                "description",
                "",
            ),
            scenario_task=scenario.get(
                "task",
                "",
            ),
            start_time=start_datetime.isoformat(),
            end_time="",
            duration_seconds=0.0,
            success=True,
            tool_calls=[],
            tool_traces=[],
            final_output="",
            metadata={
                "max_steps": max_steps,
                "timeout_seconds": timeout_seconds,
                "sandbox": "local",
                "internet_access": False,
            },
        )

        # Fresh state for this scenario.
        self.tools.reset()
        self.tools.set_trace_id(
            test_id
        )

        try:
            # ----------------------------------------------
            # Run with an actual timeout.
            # ----------------------------------------------

            with ThreadPoolExecutor(
                max_workers=1
            ) as executor:

                future = executor.submit(
                    agent.execute,
                    scenario.get(
                        "task",
                        "",
                    ),
                    max_steps,
                    timeout_seconds,
                )

                try:
                    result = future.result(
                        timeout=timeout_seconds
                    )

                except FutureTimeoutError:
                    future.cancel()

                    trace.success = False
                    trace.failure_detected = (
                        "timeout"
                    )
                    trace.failure_details = {
                        "type": "timeout",
                        "timeout_seconds": (
                            timeout_seconds
                        ),
                        "message": (
                            "Agent execution exceeded "
                            "the configured timeout."
                        ),
                    }
                    trace.error_message = (
                        "Agent execution timed out."
                    )

                    # No further result processing.
                    result = None

            # ----------------------------------------------
            # Result processing
            # ----------------------------------------------

            if result is not None:

                trace.success = bool(
                    result.get(
                        "success",
                        False,
                    )
                )

                trace.final_output = result.get(
                    "final_output",
                    "",
                )

                trace.tool_calls = result.get(
                    "tool_calls",
                    [],
                )

                trace.error_message = result.get(
                    "error_message"
                )

                if not trace.success:
                    trace.failure_detected = (
                        "execution_error"
                    )

                    trace.failure_details = {
                        "type": "agent_execution_error",
                        "message": (
                            trace.error_message
                            or "Agent execution failed."
                        ),
                    }

                # ------------------------------------------
                # Actual MockTools traces
                # ------------------------------------------

                trace.tool_traces = (
                    self.tools.get_traces()
                )

                # ------------------------------------------
                # Detect evaluator-visible failures
                # ------------------------------------------

                self._detect_failures(
                    trace
                )

                # A detected failure means this scenario
                # did not pass the evaluator.
                if trace.failure_detected:
                    trace.success = False

        except Exception as exc:
            trace.success = False
            trace.error_message = str(exc)
            trace.failure_detected = (
                "exception"
            )
            trace.failure_details = {
                "type": "runner_exception",
                "exception": str(exc),
            }

            trace.tool_traces = (
                self.tools.get_traces()
            )

        # ----------------------------------------------
        # Timing
        # ----------------------------------------------

        end_datetime = datetime.now(
            timezone.utc
        )

        trace.end_time = (
            end_datetime.isoformat()
        )

        trace.duration_seconds = (
            end_datetime
            - start_datetime
        ).total_seconds()

        # ----------------------------------------------
        # Persist
        # ----------------------------------------------

        self.traces.append(trace)

        if self.auto_persist:
            try:
                self.storage.save_trace(
                    trace.to_dict()
                )
            except Exception as storage_exc:
                trace.metadata[
                    "storage_error"
                ] = str(storage_exc)

        return trace

    # ========================================================
    # BATCH
    # ========================================================

    def run_batch(
        self,
        agent: Agent,
        scenarios: List[Dict[str, Any]],
        max_steps: int = 10,
        timeout_seconds: int = 30,
    ) -> List[ExecutionTrace]:
        """Run multiple scenarios sequentially."""

        if not isinstance(
            scenarios,
            list,
        ):
            raise TypeError(
                "scenarios must be a list."
            )

        results: List[
            ExecutionTrace
        ] = []

        total = len(
            scenarios
        )

        for index, scenario in enumerate(
            scenarios,
            start=1,
        ):
            print(
                f"Running scenario "
                f"{index}/{total}: "
                f"{scenario.get('name', 'Unnamed')}"
            )

            result = self.run_scenario(
                agent,
                scenario,
                max_steps,
                timeout_seconds,
            )

            results.append(result)

        return results

    # ========================================================
    # FAILURE DETECTION
    # ========================================================

    def _detect_failures(
        self,
        trace: ExecutionTrace,
    ) -> None:
        """
        Detect evaluator-visible failure patterns.

        Detection is intentionally based on actual recorded
        execution data, not fabricated metadata.
        """

        # ----------------------------------------------------
        # Tool execution failure
        # ----------------------------------------------------

        failed_tools = [
            call
            for call in trace.tool_calls
            if call.get("success") is False
        ]

        if failed_tools:
            first_failure = (
                failed_tools[0]
            )

            trace.failure_detected = (
                "tool_error"
            )

            trace.failure_details = {
                "type": "tool_execution_error",
                "tool_name": first_failure.get(
                    "tool_name"
                ),
                "error": first_failure.get(
                    "error"
                ),
            }

            return

        # ----------------------------------------------------
        # Repeated-tool loop
        # ----------------------------------------------------

        tool_names = [
            call.get("tool_name")
            for call in trace.tool_calls
        ]

        if len(tool_names) >= 4:
            counts = Counter(
                tool_names
            )

            repeated_tool, count = (
                counts.most_common(1)[0]
            )

            if count >= 4:
                trace.failure_detected = (
                    "loop"
                )

                trace.failure_details = {
                    "type": "loop_detection",
                    "tool_name": repeated_tool,
                    "call_count": count,
                    "message": (
                        f"Agent repeatedly called "
                        f"{repeated_tool} "
                        f"{count} times."
                    ),
                }

                return

        # ----------------------------------------------------
        # Consecutive repeated operation
        # ----------------------------------------------------

        if len(tool_names) >= 3:
            for index in range(
                len(tool_names) - 2
            ):
                window = tool_names[
                    index:index + 3
                ]

                if (
                    len(window) == 3
                    and window[0]
                    == window[1]
                    == window[2]
                ):
                    trace.failure_detected = (
                        "loop"
                    )

                    trace.failure_details = {
                        "type": (
                            "consecutive_tool_loop"
                        ),
                        "tool_name": window[0],
                        "consecutive_calls": 3,
                    }

                    return

        # ----------------------------------------------------
        # Hallucination / fabricated resource
        # ----------------------------------------------------

        for call in trace.tool_calls:
            if (
                call.get("tool_name")
                == "get_booking_details"
            ):
                result = call.get(
                    "result"
                )

                if (
                    isinstance(result, dict)
                    and result.get("found")
                    is False
                ):
                    trace.failure_detected = (
                        "hallucination"
                    )

                    trace.failure_details = {
                        "type": (
                            "hallucination_detection"
                        ),
                        "booking_id": (
                            call.get(
                                "params",
                                {},
                            ).get(
                                "booking_id"
                            )
                        ),
                        "message": (
                            "Agent requested details "
                            "for a booking that does "
                            "not exist."
                        ),
                    }

                    return

        # ----------------------------------------------------
        # Unhandled execution error
        # ----------------------------------------------------

        if not trace.success:
            if trace.failure_detected is None:
                trace.failure_detected = (
                    "execution_error"
                )

                trace.failure_details = {
                    "type": (
                        "generic_execution_failure"
                    ),
                    "message": (
                        trace.error_message
                        or "Agent failed."
                    ),
                }

    # ========================================================
    # TRACE ACCESS
    # ========================================================

    def get_latest_traces(
        self,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return latest in-memory traces."""

        if count <= 0:
            return []

        return [
            trace.to_dict()
            for trace in self.traces[-count:]
        ]

    # ========================================================
    # STATISTICS
    # ========================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Return aggregate evaluation statistics."""

        if not self.traces:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "failure_rate": 0.0,
                "failure_types": {},
                "total_tool_calls": 0,
                "average_duration_seconds": 0.0,
            }

        total = len(
            self.traces
        )

        passed = sum(
            1
            for trace in self.traces
            if trace.success
        )

        failed = (
            total - passed
        )

        failures: Dict[
            str,
            int,
        ] = {}

        total_tool_calls = 0

        for trace in self.traces:
            total_tool_calls += len(
                trace.tool_calls
            )

            if trace.failure_detected:
                failures[
                    trace.failure_detected
                ] = (
                    failures.get(
                        trace.failure_detected,
                        0,
                    )
                    + 1
                )

        average_duration = (
            sum(
                trace.duration_seconds
                for trace in self.traces
            )
            / total
        )

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (
                passed / total * 100
            ),
            "failure_rate": (
                failed / total * 100
            ),
            "failure_types": failures,
            "total_tool_calls": (
                total_tool_calls
            ),
            "average_duration_seconds": (
                round(
                    average_duration,
                    4,
                )
            ),
        }

    # ========================================================
    # RESET
    # ========================================================

    def clear_memory(self) -> None:
        """Clear in-memory execution traces."""

        self.traces.clear()


# ============================================================
# LOCAL SMOKE TEST
# ============================================================


def main() -> None:
    print(
        "🧪 Testing Sandbox Runner (Local Only)"
    )
    print("-" * 60)

    # --------------------------------------------------------
    # Create runner
    # --------------------------------------------------------

    runner = SandboxRunner(
        auto_persist=True
    )

    agent = Agent(
        name="TestAgent",
        description=(
            "Deterministic local test agent "
            "for travel scenarios."
        ),
        tools=runner.tools,
    )

    # --------------------------------------------------------
    # Scenarios
    # --------------------------------------------------------

    scenarios = [
        {
            "name": "Simple Flight Search",
            "description": (
                "Search flights from New York "
                "to London."
            ),
            "task": (
                "Search for flights from New York "
                "to London on 2026-08-25"
            ),
        },
        {
            "name": "Simple Flight Booking",
            "description": (
                "Search and book a flight."
            ),
            "task": (
                "Search for flights from New York "
                "to London on 2026-08-25 "
                "and book the first one"
            ),
        },
        {
            "name": "Hotel Search",
            "description": (
                "Find hotels in London."
            ),
            "task": (
                "Search for hotels in London "
                "from 2026-08-26 to 2026-08-28"
            ),
        },
        {
            "name": "Complex Travel Plan",
            "description": (
                "Book a flight and search for a hotel."
            ),
            "task": (
                "Book a flight from New York "
                "to London and find a hotel "
                "in London for 2 nights"
            ),
        },
        {
            "name": "Loop Test",
            "description": (
                "Agent repeatedly searches flights."
            ),
            "task": (
                "Repeat flight searches repeatedly "
                "without making a decision"
            ),
        },
        {
            "name": "Hallucination Test",
            "description": (
                "Agent requests a nonexistent booking."
            ),
            "task": (
                "Check the status of booking "
                "FAKE123 and hallucinate the details"
            ),
        },
    ]

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    print(
        "\n🚀 Running scenarios..."
    )

    results = runner.run_batch(
        agent,
        scenarios,
        max_steps=10,
        timeout_seconds=10,
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print(
        "\n📊 Results:"
    )

    for trace in results:
        status = (
            "✅ PASS"
            if trace.success
            else "❌ FAIL"
        )

        print(
            f"  {status} | "
            f"{trace.scenario_name}"
        )

        print(
            f"    Tool calls: "
            f"{len(trace.tool_calls)} | "
            f"Duration: "
            f"{trace.duration_seconds:.3f}s"
        )

        if trace.failure_detected:
            print(
                f"    ⚠️ Failure: "
                f"{trace.failure_detected}"
            )

            if trace.failure_details:
                print(
                    f"       "
                    f"{trace.failure_details}"
                )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    stats = (
        runner.get_statistics()
    )

    print(
        "\n📈 Statistics:"
    )

    print(
        f"  Total tests: "
        f"{stats['total_tests']}"
    )

    print(
        f"  Passed: "
        f"{stats['passed']}"
    )

    print(
        f"  Failed: "
        f"{stats['failed']}"
    )

    print(
        f"  Pass rate: "
        f"{stats['pass_rate']:.1f}%"
    )

    print(
        f"  Failure rate: "
        f"{stats['failure_rate']:.1f}%"
    )

    print(
        f"  Tool calls: "
        f"{stats['total_tool_calls']}"
    )

    print(
        f"  Average duration: "
        f"{stats['average_duration_seconds']:.3f}s"
    )

    print(
        f"  Failure types: "
        f"{stats['failure_types']}"
    )

    # --------------------------------------------------------
    # Persistence verification
    # --------------------------------------------------------

    stored = runner.storage.load_trace(
        results[0].test_id
    )

    assert stored is not None

    print(
        "\n💾 Persistence check: PASS"
    )

    # --------------------------------------------------------
    # Assertions
    # --------------------------------------------------------

    assert len(results) == 6

    assert (
        results[0].success is True
    )

    assert (
        results[1].success is True
    )

    assert (
        results[4].failure_detected
        == "loop"
    )

    assert (
        results[5].failure_detected
        == "hallucination"
    )

    assert (
        len(
            results[0].tool_traces
        )
        >= 1
    )

    print(
        "\n🔍 Behavioral checks: PASS"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ Sandbox Runner working locally!"
    )

    print(
        "✅ MockTools integration working!"
    )

    print(
        "✅ TraceStorage integration working!"
    )

    print(
        "🛑 No internet connection required!"
    )


if __name__ == "__main__":
    main()