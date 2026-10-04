# Architecture

## Enforcement path

```text
coding agent -> adapter -> POST /v1/events -> policy decision -> execute or pause
```

The FastAPI service is the policy decision point. An adapter sends one normalized event per proposed tool action; the service evaluates deterministic, action-aware rules, records evidence, and returns `allow`, `review`, or `hold`. A held action must not execute until an approval is resolved.

The safe demo harness calls the same event API through `POST /v1/demo/scenarios/{scenario}`. It records representative actions but never runs a command, reads a file, or sends network traffic.

## Audit and operations

PostgreSQL is the audit system of record. The React operator console reads session timelines, shows policy rationale, and submits approvals. The browser never calculates risk locally.

The workspace watcher is passive telemetry for local file changes. It is not an enforcement mechanism and cannot inspect coding-agent prompts or internal tool calls.

VFB is isolated as an optional research reference layer. A VFB outage must not affect event ingestion, scoring, approvals, or the operator console.
