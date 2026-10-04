# Agent Adapter Contract

The adapter is the enforcement boundary. It must send each proposed tool action to `POST /v1/events` before execution, then execute only when the response decision is `allow` or an explicit approval changes a held action to `allow`.

```text
agent plan -> adapter normalizes action -> policy decision -> execute or pause
```

## Required behavior

- Generate one stable `event_id` per proposed action and reuse it on retries.
- Include the agent request, inferred intent, tool type, target, and causal parent IDs.
- Treat timeouts and malformed responses as a denial for protected actions.
- Never put secret values in `target`, `agent_intent`, or metadata; use a path or secret classification instead.
- Poll `POST /v1/approvals/{approval_id}` only through a trusted local or authenticated control plane. A held action is paused, not executed.

The built-in `/v1/demo/scenarios/*` endpoints are safe simulations. They demonstrate policy behavior and intentionally never execute shell commands, access files, or make network requests.
