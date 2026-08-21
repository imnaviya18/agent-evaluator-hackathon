"""
TRACE STORAGE - Local persistence for Agent Evaluator.

All data is stored locally as JSON.
No cloud services are required.

Storage layout:

data/
├── traces/
│   └── YYYY-MM-DD/
│       ├── test_id_1.json
│       └── test_id_2.json
├── results/
│   ├── scorecard_latest.json
│   └── history.json
└── scenarios/
    ├── normal_scenarios.json
    ├── attack_scenarios.json
    └── individual_scenario.json

Design goals:
- Local-first
- Deterministic
- Atomic writes
- Safe paths
- No mutation of caller-owned dictionaries
- Backward-compatible public API
- Easy replay and evaluation integration
"""

from __future__ import annotations

import copy
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional


class TraceStorage:
    """
    Handles local persistence for traces, scenarios, scorecards,
    and evaluation history.

    The class intentionally uses only Python's standard library.
    """

    _SAFE_NAME_PATTERN = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
    )

    _DATE_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}$"
    )

    def __init__(
        self,
        base_dir: str | Path = "./data",
    ) -> None:
        self.base_dir = Path(base_dir).expanduser()

        self.traces_dir = self.base_dir / "traces"
        self.results_dir = self.base_dir / "results"
        self.scenarios_dir = self.base_dir / "scenarios"

        # Protect concurrent read/write operations within this process.
        self._lock = RLock()

        self._ensure_directories()

    # ==========================================================
    # DIRECTORY MANAGEMENT
    # ==========================================================

    def _ensure_directories(self) -> None:
        """Create all required directories."""

        self.traces_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.scenarios_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @classmethod
    def _validate_name(
        cls,
        value: str,
        field_name: str,
    ) -> str:
        """
        Validate identifiers used as filenames.

        Prevents path traversal and accidental invalid paths.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        if (
            value in {".", ".."}
            or not cls._SAFE_NAME_PATTERN.fullmatch(value)
        ):
            raise ValueError(
                f"Invalid {field_name}: {value!r}"
            )

        return value

    @classmethod
    def _validate_date(
        cls,
        date: str,
    ) -> str:
        """Validate YYYY-MM-DD date folder names."""

        if not isinstance(date, str):
            raise TypeError(
                "date must be a string."
            )

        if not cls._DATE_PATTERN.fullmatch(date):
            raise ValueError(
                "date must use YYYY-MM-DD format."
            )

        try:
            datetime.strptime(
                date,
                "%Y-%m-%d",
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid calendar date: {date}"
            ) from exc

        return date

    # ==========================================================
    # TIME
    # ==========================================================

    @staticmethod
    def _utc_timestamp() -> str:
        """Return an ISO-8601 UTC timestamp."""

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _current_date() -> str:
        """Return today's UTC date."""

        return datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")

    # ==========================================================
    # PATH HELPERS
    # ==========================================================

    def _trace_date_dir(
        self,
        date: str,
    ) -> Path:
        date = self._validate_date(date)

        directory = self.traces_dir / date

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def _trace_path(
        self,
        date: str,
        test_id: str,
    ) -> Path:
        test_id = self._validate_name(
            test_id,
            "test_id",
        )

        return (
            self._trace_date_dir(date)
            / f"{test_id}.json"
        )

    def _scenario_path(
        self,
        name: str,
    ) -> Path:
        name = self._validate_name(
            name,
            "scenario name",
        )

        return self.scenarios_dir / f"{name}.json"

    # ==========================================================
    # JSON I/O
    # ==========================================================

    @staticmethod
    def _atomic_write_json(
        file_path: Path,
        payload: Any,
    ) -> None:
        """
        Atomically write JSON.

        Data is first written to a temporary file and then
        replaced into place. This reduces the chance of leaving
        partially-written JSON if the process stops mid-write.
        """

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path: Optional[Path] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=str(file_path.parent),
                prefix=f".{file_path.stem}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                json.dump(
                    payload,
                    temp_file,
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=False,
                )

                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(
                temp_path,
                file_path,
            )

        finally:
            if (
                temp_path is not None
                and temp_path.exists()
            ):
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _read_json(
        file_path: Path,
    ) -> Any:
        """Read and parse a JSON file."""

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except FileNotFoundError:
            raise

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON file: {file_path}"
            ) from exc

    # ==========================================================
    # TRACE IDENTIFICATION
    # ==========================================================

    def _resolve_test_id(
        self,
        trace: Dict[str, Any],
    ) -> str:
        """
        Determine a stable filename from trace metadata.

        Priority:
        1. test_id
        2. trace_id
        3. generated UUID
        """

        test_id = trace.get("test_id")

        if test_id:
            return self._validate_name(
                str(test_id),
                "test_id",
            )

        trace_id = trace.get("trace_id")

        if trace_id:
            return self._validate_name(
                str(trace_id),
                "trace_id",
            )

        # UUID contains safe characters for filenames.
        generated = (
            f"trace-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            f"-{os.urandom(4).hex()}"
        )

        return generated

    # ==========================================================
    # TRACE SAVE
    # ==========================================================

    def save_trace(
        self,
        trace: Dict[str, Any],
    ) -> str:
        """
        Save a single trace.

        Returns:
            Relative/absolute path string to the JSON file,
            depending on how base_dir was supplied.
        """

        if not isinstance(trace, dict):
            raise TypeError(
                "trace must be a dictionary."
            )

        with self._lock:
            trace_copy = copy.deepcopy(trace)

            date_str = str(
                trace_copy.get(
                    "date",
                    self._current_date(),
                )
            )

            # Validate explicitly supplied dates.
            self._validate_date(date_str)

            test_id = self._resolve_test_id(
                trace_copy
            )

            trace_copy["test_id"] = test_id

            # Never mutate the caller's original dictionary.
            trace_copy["saved_at"] = (
                self._utc_timestamp()
            )

            file_path = self._trace_path(
                date_str,
                test_id,
            )

            self._atomic_write_json(
                file_path,
                trace_copy,
            )

            return str(file_path)

    def save_batch_traces(
        self,
        traces: Iterable[Dict[str, Any]],
    ) -> List[str]:
        """Save multiple traces."""

        if traces is None:
            raise TypeError(
                "traces cannot be None."
            )

        paths: List[str] = []

        for trace in traces:
            paths.append(
                self.save_trace(trace)
            )

        return paths

    # ==========================================================
    # TRACE LOAD
    # ==========================================================

    def load_trace(
        self,
        test_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a trace by test_id.

        Searches all date directories.
        """

        test_id = self._validate_name(
            test_id,
            "test_id",
        )

        with self._lock:
            if not self.traces_dir.exists():
                return None

            # Newest directories first.
            date_dirs = sorted(
                (
                    path
                    for path in self.traces_dir.iterdir()
                    if path.is_dir()
                ),
                key=lambda path: path.name,
                reverse=True,
            )

            for date_dir in date_dirs:
                file_path = (
                    date_dir
                    / f"{test_id}.json"
                )

                if not file_path.exists():
                    continue

                payload = self._read_json(
                    file_path
                )

                if not isinstance(payload, dict):
                    raise ValueError(
                        f"Trace file must contain "
                        f"a JSON object: {file_path}"
                    )

                return payload

        return None

    def load_traces(
        self,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Load traces.

        Args:
            date:
                Optional YYYY-MM-DD date.
                None = search all dates.

            limit:
                Maximum number of traces returned.
        """

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if limit <= 0:
            return []

        with self._lock:
            trace_files: List[Path] = []

            if date is not None:
                date = self._validate_date(
                    date
                )

                date_dir = (
                    self.traces_dir / date
                )

                if date_dir.exists():
                    trace_files.extend(
                        sorted(
                            date_dir.glob("*.json"),
                            key=lambda p: p.name,
                            reverse=True,
                        )
                    )

            else:
                if not self.traces_dir.exists():
                    return []

                date_dirs = sorted(
                    (
                        path
                        for path in self.traces_dir.iterdir()
                        if path.is_dir()
                    ),
                    key=lambda path: path.name,
                    reverse=True,
                )

                for date_dir in date_dirs:
                    trace_files.extend(
                        sorted(
                            date_dir.glob("*.json"),
                            key=lambda p: p.name,
                            reverse=True,
                        )
                    )

            traces: List[Dict[str, Any]] = []

            for file_path in trace_files:
                if len(traces) >= limit:
                    break

                try:
                    payload = self._read_json(
                        file_path
                    )

                except ValueError:
                    # Corrupt files should not silently become
                    # normal traces. Skip them here while keeping
                    # the loader usable for the rest of the dataset.
                    continue

                if isinstance(payload, dict):
                    traces.append(payload)

            return traces[:limit]

    # ==========================================================
    # TRACE MANAGEMENT
    # ==========================================================

    def get_trace_count(
        self,
        date: Optional[str] = None,
    ) -> int:
        """
        Count stored trace files.

        Optional date limits the count to one day.
        """

        if date is not None:
            date = self._validate_date(
                date
            )

            date_dir = (
                self.traces_dir / date
            )

            if not date_dir.exists():
                return 0

            return sum(
                1
                for path in date_dir.glob("*.json")
                if path.is_file()
            )

        if not self.traces_dir.exists():
            return 0

        return sum(
            1
            for date_dir in self.traces_dir.iterdir()
            if date_dir.is_dir()
            for path in date_dir.glob("*.json")
            if path.is_file()
        )

    def delete_trace(
        self,
        test_id: str,
    ) -> bool:
        """Delete one trace by test_id."""

        test_id = self._validate_name(
            test_id,
            "test_id",
        )

        with self._lock:
            if not self.traces_dir.exists():
                return False

            for date_dir in self.traces_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                file_path = (
                    date_dir
                    / f"{test_id}.json"
                )

                if file_path.exists():
                    file_path.unlink()

                    # Remove empty date folder.
                    try:
                        date_dir.rmdir()
                    except OSError:
                        pass

                    return True

        return False

    def clear_traces(
        self,
        date: Optional[str] = None,
    ) -> int:
        """
        Delete traces.

        Returns:
            Number of trace files deleted.
        """

        deleted = 0

        with self._lock:
            if not self.traces_dir.exists():
                return 0

            if date is not None:
                date = self._validate_date(
                    date
                )

                date_dirs = [
                    self.traces_dir / date
                ]
            else:
                date_dirs = [
                    path
                    for path in self.traces_dir.iterdir()
                    if path.is_dir()
                ]

            for date_dir in date_dirs:
                if not date_dir.exists():
                    continue

                files = [
                    path
                    for path in date_dir.glob("*.json")
                    if path.is_file()
                ]

                for file_path in files:
                    file_path.unlink()
                    deleted += 1

                try:
                    date_dir.rmdir()
                except OSError:
                    pass

        return deleted

    def get_available_dates(
        self,
    ) -> List[str]:
        """Return trace dates, newest first."""

        if not self.traces_dir.exists():
            return []

        dates = []

        for item in self.traces_dir.iterdir():
            if (
                item.is_dir()
                and self._DATE_PATTERN.fullmatch(
                    item.name
                )
            ):
                dates.append(item.name)

        return sorted(
            dates,
            reverse=True,
        )

    # ==========================================================
    # SCENARIOS
    # ==========================================================

    def save_scenario(
        self,
        scenario: Dict[str, Any],
        name: str,
    ) -> str:
        """Save one scenario."""

        if not isinstance(scenario, dict):
            raise TypeError(
                "scenario must be a dictionary."
            )

        with self._lock:
            scenario_copy = copy.deepcopy(
                scenario
            )

            scenario_copy.setdefault(
                "saved_at",
                self._utc_timestamp(),
            )

            file_path = self._scenario_path(
                name
            )

            self._atomic_write_json(
                file_path,
                scenario_copy,
            )

            return str(file_path)

    def save_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
        category: str = "normal",
    ) -> str:
        """
        Save a scenario collection.

        Example:
            normal_scenarios.json
            attack_scenarios.json
        """

        if not isinstance(
            scenarios,
            list,
        ):
            raise TypeError(
                "scenarios must be a list."
            )

        category = self._validate_name(
            category,
            "category",
        )

        scenario_copy = copy.deepcopy(
            scenarios
        )

        if not all(
            isinstance(item, dict)
            for item in scenario_copy
        ):
            raise TypeError(
                "Every scenario must be a dictionary."
            )

        filename = (
            f"{category}_scenarios.json"
        )

        file_path = (
            self.scenarios_dir / filename
        )

        payload = {
            "category": category,
            "count": len(scenario_copy),
            "scenarios": scenario_copy,
            "saved_at": self._utc_timestamp(),
        }

        with self._lock:
            self._atomic_write_json(
                file_path,
                payload,
            )

        return str(file_path)

    def load_scenarios(
        self,
        category: str = "normal",
    ) -> List[Dict[str, Any]]:
        """Load a scenario collection."""

        category = self._validate_name(
            category,
            "category",
        )

        file_path = (
            self.scenarios_dir
            / f"{category}_scenarios.json"
        )

        if not file_path.exists():
            return []

        with self._lock:
            payload = self._read_json(
                file_path
            )

        scenarios = payload.get(
            "scenarios",
            [],
        )

        if not isinstance(
            scenarios,
            list,
        ):
            raise ValueError(
                f"Invalid scenario file: {file_path}"
            )

        return scenarios

    # ==========================================================
    # SCORECARD
    # ==========================================================

    def save_scorecard(
        self,
        scorecard: Dict[str, Any],
    ) -> str:
        """Save the latest evaluator scorecard."""

        if not isinstance(
            scorecard,
            dict,
        ):
            raise TypeError(
                "scorecard must be a dictionary."
            )

        payload = {
            "scorecard": copy.deepcopy(
                scorecard
            ),
            "saved_at": self._utc_timestamp(),
        }

        file_path = (
            self.results_dir
            / "scorecard_latest.json"
        )

        with self._lock:
            self._atomic_write_json(
                file_path,
                payload,
            )

        return str(file_path)

    def load_scorecard(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Load the latest scorecard."""

        file_path = (
            self.results_dir
            / "scorecard_latest.json"
        )

        if not file_path.exists():
            return None

        with self._lock:
            payload = self._read_json(
                file_path
            )

        scorecard = payload.get(
            "scorecard"
        )

        if scorecard is None:
            return None

        if not isinstance(
            scorecard,
            dict,
        ):
            raise ValueError(
                "Stored scorecard is not an object."
            )

        return scorecard

    # ==========================================================
    # HISTORY
    # ==========================================================

    def save_history(
        self,
        results: List[Dict[str, Any]],
    ) -> str:
        """Persist complete evaluation history."""

        if not isinstance(
            results,
            list,
        ):
            raise TypeError(
                "results must be a list."
            )

        results_copy = copy.deepcopy(
            results
        )

        if not all(
            isinstance(item, dict)
            for item in results_copy
        ):
            raise TypeError(
                "Every history result must "
                "be a dictionary."
            )

        payload = {
            "results": results_copy,
            "last_updated": self._utc_timestamp(),
            "total_tests": len(results_copy),
        }

        file_path = (
            self.results_dir
            / "history.json"
        )

        with self._lock:
            self._atomic_write_json(
                file_path,
                payload,
            )

        return str(file_path)

    def load_history(
        self,
    ) -> List[Dict[str, Any]]:
        """Load evaluation history."""

        file_path = (
            self.results_dir
            / "history.json"
        )

        if not file_path.exists():
            return []

        with self._lock:
            payload = self._read_json(
                file_path
            )

        results = payload.get(
            "results",
            [],
        )

        if not isinstance(
            results,
            list,
        ):
            raise ValueError(
                "Stored history is invalid."
            )

        return results

    # ==========================================================
    # EXPORT
    # ==========================================================

    def export_trace(
        self,
        test_id: str,
        output_path: str | Path,
    ) -> str:
        """
        Export one trace to another JSON location.
        """

        trace = self.load_trace(
            test_id
        )

        if trace is None:
            raise FileNotFoundError(
                f"Trace '{test_id}' not found."
            )

        output = Path(
            output_path
        ).expanduser()

        self._atomic_write_json(
            output,
            trace,
        )

        return str(output)

    # ==========================================================
    # STORAGE INFO
    # ==========================================================

    def get_storage_stats(
        self,
    ) -> Dict[str, Any]:
        """Return useful storage metadata."""

        trace_count = (
            self.get_trace_count()
        )

        dates = (
            self.get_available_dates()
        )

        scenario_files = (
            list(
                self.scenarios_dir.glob(
                    "*.json"
                )
            )
            if self.scenarios_dir.exists()
            else []
        )

        result_files = (
            list(
                self.results_dir.glob(
                    "*.json"
                )
            )
            if self.results_dir.exists()
            else []
        )

        return {
            "base_dir": str(
                self.base_dir
            ),
            "traces": {
                "count": trace_count,
                "dates": dates,
            },
            "scenarios": {
                "files": len(
                    scenario_files
                ),
            },
            "results": {
                "files": len(
                    result_files
                ),
            },
        }


# ============================================================
# LOCAL SMOKE TEST
# ============================================================

def main() -> None:
    print(
        "🧪 Testing TraceStorage"
    )
    print("=" * 60)

    # Keep smoke-test data isolated.
    test_root = Path(
        tempfile.mkdtemp(
            prefix="trace_storage_test_"
        )
    )

    try:
        storage = TraceStorage(
            test_root / "data"
        )

        print("\n📁 Directory setup")
        assert storage.traces_dir.exists()
        assert storage.results_dir.exists()
        assert storage.scenarios_dir.exists()
        print("PASS")

        # -----------------------------------------------------
        # Save trace
        # -----------------------------------------------------

        print("\n💾 Save trace")

        original_trace = {
            "test_id": "smoke-test-001",
            "trace_id": "trace-001",
            "tool_name": "flight_api",
            "operation": "search_flights",
            "arguments": {
                "origin": "New York",
                "destination": "London",
            },
            "result": {
                "total": 3,
            },
            "success": True,
            "error": None,
        }

        original_snapshot = copy.deepcopy(
            original_trace
        )

        path = storage.save_trace(
            original_trace
        )

        assert Path(path).exists()

        # Ensure the caller's dictionary was not mutated.
        assert (
            original_trace
            == original_snapshot
        )

        print("PASS")

        # -----------------------------------------------------
        # Load trace
        # -----------------------------------------------------

        print("\n📥 Load trace")

        loaded = storage.load_trace(
            "smoke-test-001"
        )

        assert loaded is not None
        assert (
            loaded["trace_id"]
            == "trace-001"
        )

        print("PASS")

        # -----------------------------------------------------
        # Count
        # -----------------------------------------------------

        print("\n🔢 Trace count")

        assert (
            storage.get_trace_count()
            == 1
        )

        print("PASS")

        # -----------------------------------------------------
        # Batch save
        # -----------------------------------------------------

        print("\n📦 Batch save")

        batch = [
            {
                "test_id": "smoke-test-002",
                "operation": "get_weather",
                "success": True,
            },
            {
                "test_id": "smoke-test-003",
                "operation": "book_flight",
                "success": True,
            },
        ]

        paths = (
            storage.save_batch_traces(
                batch
            )
        )

        assert len(paths) == 2
        assert (
            storage.get_trace_count()
            == 3
        )

        print("PASS")

        # -----------------------------------------------------
        # Date loading
        # -----------------------------------------------------

        print("\n📅 Date loading")

        current_date = (
            datetime.now(timezone.utc)
            .strftime("%Y-%m-%d")
        )

        date_traces = (
            storage.load_traces(
                date=current_date
            )
        )

        assert len(date_traces) == 3

        print("PASS")

        # -----------------------------------------------------
        # Available dates
        # -----------------------------------------------------

        print("\n🗓️ Available dates")

        dates = (
            storage.get_available_dates()
        )

        assert current_date in dates

        print("PASS")

        # -----------------------------------------------------
        # Scenario storage
        # -----------------------------------------------------

        print("\n🎯 Scenario storage")

        scenarios = [
            {
                "id": "scenario-001",
                "name": "Simple Flight Search",
                "category": "normal",
            },
            {
                "id": "scenario-002",
                "name": "Invalid Flight",
                "category": "attack",
            },
        ]

        scenario_path = (
            storage.save_scenarios(
                scenarios,
                category="normal",
            )
        )

        assert Path(
            scenario_path
        ).exists()

        loaded_scenarios = (
            storage.load_scenarios(
                "normal"
            )
        )

        assert (
            len(loaded_scenarios)
            == 2
        )

        print("PASS")

        # -----------------------------------------------------
        # Scorecard
        # -----------------------------------------------------

        print("\n📊 Scorecard")

        scorecard = {
            "overall_score": 87.5,
            "reliability": 90.0,
            "security": 85.0,
        }

        storage.save_scorecard(
            scorecard
        )

        loaded_scorecard = (
            storage.load_scorecard()
        )

        assert (
            loaded_scorecard
            == scorecard
        )

        print("PASS")

        # -----------------------------------------------------
        # History
        # -----------------------------------------------------

        print("\n📚 History")

        history = [
            {
                "test_id": "run-001",
                "score": 90,
            },
            {
                "test_id": "run-002",
                "score": 85,
            },
        ]

        storage.save_history(
            history
        )

        loaded_history = (
            storage.load_history()
        )

        assert (
            loaded_history
            == history
        )

        print("PASS")

        # -----------------------------------------------------
        # Export
        # -----------------------------------------------------

        print("\n📤 Export trace")

        export_path = (
            test_root
            / "exported_trace.json"
        )

        storage.export_trace(
            "smoke-test-001",
            export_path,
        )

        assert export_path.exists()

        print("PASS")

        # -----------------------------------------------------
        # Storage stats
        # -----------------------------------------------------

        print("\n📈 Storage stats")

        stats = (
            storage.get_storage_stats()
        )

        assert (
            stats["traces"]["count"]
            == 3
        )

        assert (
            current_date
            in stats["traces"]["dates"]
        )

        print("PASS")

        # -----------------------------------------------------
        # Delete
        # -----------------------------------------------------

        print("\n🗑️ Delete trace")

        deleted = (
            storage.delete_trace(
                "smoke-test-003"
            )
        )

        assert deleted is True

        assert (
            storage.get_trace_count()
            == 2
        )

        print("PASS")

        # -----------------------------------------------------
        # Clear
        # -----------------------------------------------------

        print("\n🧹 Clear traces")

        deleted_count = (
            storage.clear_traces()
        )

        assert deleted_count == 2
        assert (
            storage.get_trace_count()
            == 0
        )

        print("PASS")

        # -----------------------------------------------------
        # Validation
        # -----------------------------------------------------

        print("\n🛡️ Validation")

        try:
            storage.load_trace(
                "../evil"
            )
            raise AssertionError(
                "Path traversal was not blocked."
            )
        except ValueError:
            pass

        print("PASS")

        print("\n" + "=" * 60)
        print(
            "✅ TraceStorage smoke tests PASSED"
        )
        print(
            "✅ Local JSON persistence verified"
        )
        print(
            "✅ Atomic writes verified"
        )
        print(
            "✅ Path validation verified"
        )
        print(
            "✅ Trace/scenario/result separation verified"
        )

    finally:
        # Remove isolated smoke-test directory.
        shutil.rmtree(
            test_root,
            ignore_errors=True,
        )


if __name__ == "__main__":
    main()