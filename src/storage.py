"""
Local JSON-based storage for scenarios, attacks, and results.
No database needed — everything is flat files under data/.
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
SCENARIOS_DIR = DATA_DIR / "scenarios"
ATTACKS_DIR = DATA_DIR / "attacks"
RESULTS_DIR = DATA_DIR / "results"


def _ensure_dirs():
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    ATTACKS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_scenarios(scenarios: dict, filename: str = "scenarios.json") -> Path:
    _ensure_dirs()
    path = SCENARIOS_DIR / filename
    with open(path, "w") as f:
        json.dump(scenarios, f, indent=2)
    return path


def load_scenarios(filename: str = "scenarios.json") -> dict:
    path = SCENARIOS_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_attacks(attacks: dict, filename: str = "attack_scenarios.json") -> Path:
    _ensure_dirs()
    path = ATTACKS_DIR / filename
    with open(path, "w") as f:
        json.dump(attacks, f, indent=2)
    return path


def load_attacks(filename: str = "attack_scenarios.json") -> dict:
    path = ATTACKS_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_results(results: dict, test_id: str) -> Path:
    _ensure_dirs()
    path = RESULTS_DIR / f"{test_id}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return path


def load_results(test_id: str) -> dict | None:
    path = RESULTS_DIR / f"{test_id}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def get_history() -> list[dict]:
    """Return a summary of all previous test results, most recent first."""
    _ensure_dirs()
    history = []
    for path in sorted(RESULTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(path, "r") as f:
            data = json.load(f)
        history.append({
            "test_id": data.get("test_id"),
            "timestamp": data.get("timestamp"),
            "agent_description": data.get("agent_description"),
            "pass_rate": data.get("scorecard", {}).get("pass_rate"),
            "security_score": data.get("security_scorecard", {}).get("security_score"),
        })
    return history