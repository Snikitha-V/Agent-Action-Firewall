"""Local filesystem telemetry for demos and agent integrations.

This sensor observes file changes only. It does not inspect prompts, model output,
or terminal commands, which must be supplied by an explicit agent adapter.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import settings
from .db import SessionLocal
from .models import ApprovalRecord, EventRecord
from .rules import evaluate
from .schemas import EventIn

LOG = logging.getLogger(__name__)
IGNORED_PARTS = {".git", "node_modules", "__pycache__", ".pytest_cache", "dist"}


class WorkspaceHandler(FileSystemEventHandler):
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.last_seen: dict[str, float] = {}

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if IGNORED_PARTS.intersection(path.parts) or path.name.endswith((".pyc", ".swp", "~")):
            return
        key, now = str(path), time.monotonic()
        if now - self.last_seen.get(key, 0) < 1:
            return
        self.last_seen[key] = now
        self._record(path)

    def _record(self, path: Path) -> None:
        try:
            target = str(path.resolve().relative_to(self.root))
        except ValueError:
            return
        event = EventIn(
            run_id=settings.monitored_run_id,
            user_request="Observe local coding-agent workspace activity",
            agent_intent="Record a file modification from the local workspace sensor",
            tool_name="workspace_watcher",
            action_type="file_write",
            target=target,
            metadata={"source": "workspace_watcher"},
        )
        score, decision, evidence = evaluate(event)
        db = SessionLocal()
        try:
            record = EventRecord(
                event_id=str(uuid.uuid4()), run_id=event.run_id,
                timestamp=datetime.now(timezone.utc), user_request=event.user_request,
                agent_intent=event.agent_intent, tool_name=event.tool_name,
                action_type=event.action_type, target=event.target,
                parent_event_ids=[], metadata_json=event.metadata, risk_score=score,
                decision=decision, evidence=evidence,
            )
            db.add(record)
            db.flush()
            if decision == "hold":
                db.add(ApprovalRecord(event_id=record.event_id))
            db.commit()
            LOG.info("Recorded workspace activity for %s", target)
        except Exception:
            db.rollback()
            LOG.exception("Could not record workspace activity")
        finally:
            db.close()


def start_workspace_monitor() -> Observer | None:
    if not settings.monitored_workspace:
        return None
    root = Path(settings.monitored_workspace)
    if not root.is_dir():
        LOG.warning("Workspace monitor path does not exist: %s", root)
        return None
    observer = Observer()
    observer.schedule(WorkspaceHandler(root), str(root), recursive=True)
    observer.start()
    LOG.info("Watching local workspace: %s", root)
    return observer
