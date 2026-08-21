import json
from datetime import datetime, timezone
from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from app.database import BaseModel


class AgentModel(BaseModel):
    """Stores agent configuration details."""
    name = CharField(max_length=120, index=True)
    description = TextField(default="")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TestRunModel(BaseModel):
    """Stores aggregate information about a batch test execution."""
    test_id = CharField(max_length=120, unique=True, index=True)
    agent_name = CharField(max_length=120, index=True)
    agent_description = TextField(default="")
    total_scenarios = IntegerField(default=0)
    passed_count = IntegerField(default=0)
    failed_count = IntegerField(default=0)
    pass_rate = FloatField(default=0.0)
    total_tool_calls = IntegerField(default=0)
    average_duration_seconds = FloatField(default=0.0)
    failure_breakdown_json = TextField(default="{}")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        try:
            breakdown = json.loads(self.failure_breakdown_json)
        except Exception:
            breakdown = {}
        return {
            "test_id": self.test_id,
            "agent_name": self.agent_name,
            "agent_description": self.agent_description,
            "total_scenarios": self.total_scenarios,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "pass_rate": self.pass_rate,
            "total_tool_calls": self.total_tool_calls,
            "average_duration_seconds": self.average_duration_seconds,
            "failure_breakdown": breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "results": [r.to_dict() for r in self.scenario_results],
        }


class ScenarioResultModel(BaseModel):
    """Stores detailed execution trace and result for a single scenario."""
    test_run = ForeignKeyField(TestRunModel, backref="scenario_results", on_delete="CASCADE")
    scenario_name = CharField(max_length=255)
    task = TextField(default="")
    success = BooleanField(default=True)
    failure_detected = CharField(max_length=100, null=True)
    failure_details_json = TextField(null=True)
    duration_seconds = FloatField(default=0.0)
    tool_calls_json = TextField(default="[]")
    final_output = TextField(null=True)
    error_message = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        try:
            tool_calls = json.loads(self.tool_calls_json)
        except Exception:
            tool_calls = []
        try:
            failure_details = json.loads(self.failure_details_json) if self.failure_details_json else None
        except Exception:
            failure_details = None
        return {
            "scenario_name": self.scenario_name,
            "task": self.task,
            "success": self.success,
            "failure_detected": self.failure_detected,
            "failure_details": failure_details,
            "duration_seconds": self.duration_seconds,
            "tool_calls": tool_calls,
            "final_output": self.final_output,
            "error_message": self.error_message,
        }


class ScorecardModel(BaseModel):
    """Stores persistent scorecard ratings for an agent."""
    agent_name = CharField(max_length=120, unique=True, index=True)
    reliability_score = FloatField(default=0.0)
    security_score = FloatField(default=0.0)
    total_evaluations = IntegerField(default=0)
    raw_stats_json = TextField(default="{}")
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        try:
            raw_stats = json.loads(self.raw_stats_json)
        except Exception:
            raw_stats = {}
        return {
            "agent_name": self.agent_name,
            "reliability_score": self.reliability_score,
            "security_score": self.security_score,
            "total_evaluations": self.total_evaluations,
            "statistics": raw_stats,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
