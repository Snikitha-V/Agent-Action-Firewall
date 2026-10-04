# Agent Action Firewall

**A policy gateway and investigation console for AI coding agents.**

Agent Action Firewall gives engineering teams visibility and control over what agents try to do in a shared repository. Before a protected tool action runs, an adapter can ask the Firewall to allow it, flag it for review, or hold it for an operator decision.

Inspired by the public Hugging Face incident involving OpenAI evaluation agents, the project focuses on a simple security question: when several agents work toward one task, can an engineer see the action path before a risky command, secret read, or outbound transfer becomes damage?

## What it covers

- Prompt-injection and instruction-override signals
- Sensitive files, credentials, and environment access
- Destructive shell commands and force pushes
- Dependency and protected CI/configuration changes
- Outbound transfers and secret-exfiltration chains
- Explainable policy evidence, risk scores, and approval decisions

```text
Agent planner / worker / reviewer
              |
              | proposed tool action
              v
     Agent Action Firewall API
              |
      +-------+--------+
      |                |
   allow             hold
      |                |
      v                v
protected tool     operator decision
execution          approve / deny
      |
      v
  durable audit trail + investigation dashboard
```

## VFB-inspired investigation

[Virtual Fly Brain (VFB)](https://www.virtualflybrain.org/) is an inspiration, not a required dependency or detection engine. A neural circuit becomes useful when each connection can be inspected as part of a pathway. Agent Action Firewall applies that idea to agent behavior: a prompt, file read, command, and network request may be harmless independently but suspicious as a connected sequence.

The project stores run IDs and parent-event IDs today. The roadmap is a VFB-inspired map of agent roles, handoffs, and causal action paths for multi-agent investigations.

## Run it

```bash
cp .env.example .env
docker compose up --build
```

Open the dashboard at [http://localhost:5173](http://localhost:5173) and API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

Choose **Injection chain** in the dashboard to see a safe, deterministic prompt-injection-to-secret-access-to-exfiltration scenario. The demo never executes shell commands, reads real secrets, or contacts external services.

## What is real today

| Capability | Status |
| --- | --- |
| FastAPI policy API, PostgreSQL audit store, React dashboard, and approval flow | Implemented |
| Safe attack-path scenarios and deterministic rules | Implemented |
| Passive observation of actual file saves in this repository | Implemented |
| Enforcement through an explicit agent adapter, wrapper, or MCP tool host | API contract ready; integration is next |
| Inspection of Codex private prompts, reasoning, or internal tool calls | Not possible and not claimed |

The **This workspace** dashboard view is passive telemetry: it observes file changes after they happen. Real prevention requires a coding-agent integration to call the API before it invokes a protected tool.

## Development

```bash
cd apps/api
pytest
ruff check .
```

Read the [architecture](docs/architecture.md), [agent adapter contract](docs/agent-adapter.md), [threat model](docs/threat-model.md), and [rule authoring guide](docs/rule-authoring.md) for the deeper technical details.

## Roadmap

- Add a controlled MCP tool gateway for pre-execution enforcement.
- Model agent identity, roles, delegation, and shared-task correlation.
- Build the multi-agent causal investigation map.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution standards.
