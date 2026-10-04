import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .activity import start_workspace_monitor
from .db import Base, engine, get_db
from .models import ApprovalRecord, EventRecord
from .rules import RULES, evaluate
from .demo import SCENARIOS
from .schemas import ApprovalIn, DemoRunOut, EventIn, EventOut

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    observer = start_workspace_monitor()
    yield
    if observer:
        observer.stop()
        observer.join(timeout=5)


app = FastAPI(title="LLM Agent Threat Mapper", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=False)


def event_out(record: EventRecord, approval: ApprovalRecord | None = None) -> EventOut:
    return EventOut(
        event_id=record.event_id,
        run_id=record.run_id,
        risk_score=record.risk_score,
        decision=record.decision,
        evidence=record.evidence,
        approval_id=approval.approval_id if approval else None,
        execution_status=record.metadata_json.get("execution_status", "proposed"),
    )


def persist_event(event: EventIn, db: Session) -> EventOut:
    if event.event_id:
        existing = db.get(EventRecord, event.event_id)
        if existing:
            approval = db.query(ApprovalRecord).filter_by(event_id=existing.event_id).first()
            return event_out(existing, approval)

    score, decision, evidence = evaluate(event)
    metadata = dict(event.metadata)
    metadata.setdefault("execution_status", "held" if decision == "hold" else "allowed")
    record = EventRecord(
        event_id=event.event_id or str(uuid.uuid4()),
        run_id=event.run_id,
        timestamp=event.timestamp or datetime.now(timezone.utc),
        user_request=event.user_request,
        agent_intent=event.agent_intent,
        tool_name=event.tool_name,
        action_type=event.action_type,
        target=event.target,
        parent_event_ids=event.parent_event_ids,
        metadata_json=metadata,
        risk_score=score,
        decision=decision,
        evidence=evidence,
    )
    db.add(record)
    db.flush()
    approval = ApprovalRecord(event_id=record.event_id) if decision == "hold" else None
    if approval:
        db.add(approval)
    db.commit()
    return event_out(record, approval)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    from sqlalchemy import text
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/v1/events", response_model=EventOut, status_code=201)
def create_event(event: EventIn, db: Session = Depends(get_db)):
    return persist_event(event, db)


@app.post("/v1/demo/scenarios/{scenario}", response_model=DemoRunOut)
def run_demo_scenario(scenario: str, db: Session = Depends(get_db)):
    definition = SCENARIOS.get(scenario)
    if not definition:
        raise HTTPException(404, "Demo scenario not found")

    user_request, actions = definition
    run_id = f"demo-{scenario}"
    old_events = db.query(EventRecord).filter_by(run_id=run_id).all()
    for old_event in old_events:
        db.query(ApprovalRecord).filter_by(event_id=old_event.event_id).delete()
        db.delete(old_event)
    db.commit()

    parents: list[str] = []
    for action in actions:
        created = persist_event(EventIn(
            run_id=run_id,
            user_request=user_request,
            agent_intent=action.agent_intent,
            tool_name=action.tool_name,
            action_type=action.action_type,
            target=action.target,
            parent_event_ids=parents[-1:],
            metadata={"source": "safe_demo_harness", "execution_status": "simulated"},
        ), db)
        parents.append(created.event_id)
    return DemoRunOut(run_id=run_id, scenario=scenario, events_created=len(actions))


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    events = db.query(EventRecord).filter_by(run_id=run_id).order_by(EventRecord.timestamp).all()
    payload = []
    for event in events:
        approval = db.query(ApprovalRecord).filter_by(event_id=event.event_id).first()
        payload.append({"event_id": event.event_id, "timestamp": event.timestamp, "tool_name": event.tool_name, "action_type": event.action_type, "target": event.target, "parent_event_ids": event.parent_event_ids, "risk_score": event.risk_score, "decision": event.decision, "evidence": event.evidence, "approval_id": approval.approval_id if approval else None, "execution_status": event.metadata_json.get("execution_status", "proposed"), "agent_intent": event.agent_intent, "user_request": event.user_request})
    return {"run_id": run_id, "events": payload}


@app.get("/v1/incidents")
def incidents(db: Session = Depends(get_db)):
    rows = db.query(EventRecord).filter(EventRecord.decision.in_(["hold", "deny", "review"])).order_by(EventRecord.timestamp.desc()).limit(100).all()
    return [{"event_id": e.event_id, "run_id": e.run_id, "target": e.target, "risk_score": e.risk_score, "decision": e.decision, "timestamp": e.timestamp} for e in rows]


@app.post("/v1/approvals/{approval_id}")
def decide(approval_id: str, payload: ApprovalIn, db: Session = Depends(get_db)):
    approval = db.get(ApprovalRecord, approval_id)
    if not approval:
        raise HTTPException(404, "Approval request not found")
    if approval.status != "pending":
        raise HTTPException(409, "Approval was already decided")
    approval.status, approval.reason, approval.decided_at = payload.decision, payload.reason, datetime.now(timezone.utc)
    event = db.get(EventRecord, approval.event_id)
    event.decision = payload.decision
    event.metadata_json = {**event.metadata_json, "execution_status": "approved" if payload.decision == "allow" else "denied"}
    db.commit()
    return {"approval_id": approval_id, "status": approval.status}


@app.get("/v1/rules")
def rules():
    return [{"rule_id": r.rule_id, "label": r.label, "score": r.score, "explanation": r.explanation, "version": "1.0.0"} for r in RULES]
