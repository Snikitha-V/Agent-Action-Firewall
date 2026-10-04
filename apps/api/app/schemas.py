from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ActionType = Literal["shell", "file_read", "file_write", "network", "git", "package", "env"]
Decision = Literal["allow", "review", "hold", "deny"]


class EventIn(BaseModel):
    event_id: str | None = None
    run_id: str = Field(min_length=1, max_length=128)
    timestamp: datetime | None = None
    user_request: str = Field(min_length=1, max_length=10_000)
    agent_intent: str = Field(default="", max_length=10_000)
    tool_name: str = Field(min_length=1, max_length=100)
    action_type: ActionType
    target: str = Field(min_length=1, max_length=20_000)
    parent_event_ids: list[str] = Field(default_factory=list, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    rule_id: str
    label: str
    score: int
    explanation: str


class EventOut(BaseModel):
    event_id: str
    run_id: str
    risk_score: float
    decision: Decision
    evidence: list[Evidence]
    approval_id: str | None = None
    execution_status: str = "proposed"


class DemoRunOut(BaseModel):
    run_id: str
    scenario: str
    events_created: int


class ApprovalIn(BaseModel):
    decision: Literal["allow", "deny"]
    reason: str = Field(min_length=1, max_length=2_000)
