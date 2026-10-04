import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class EventRecord(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(128), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user_request: Mapped[str] = mapped_column(Text)
    agent_intent: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str] = mapped_column(String(100))
    action_type: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(Text)
    parent_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    decision: Mapped[str] = mapped_column(String(16), default="allow")
    evidence: Mapped[list] = mapped_column(JSON, default=list)


class ApprovalRecord(Base):
    __tablename__ = "approvals"
    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.event_id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
