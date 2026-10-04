# Operations

Run locally with `docker compose up --build`. The API exposes `/health` for liveness and `/ready` for database readiness. Back up PostgreSQL before any schema migration; production migrations must be applied as a separate release step.

Treat event targets and metadata as potentially sensitive. Do not log credentials, authorization headers, raw environment values, or approval reasons beyond the approved retention policy.
