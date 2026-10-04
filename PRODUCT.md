# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Software engineers and security-minded platform teams using coding agents in local repositories.

## Product Purpose

LLM Agent Threat Mapper is a local-first policy gateway that evaluates a coding agent's proposed tool action before execution. It makes risky actions reviewable and produces an auditable record of the decision.

## Positioning

The product evaluates normalized agent tool calls at the point of execution rather than inferring risk only from prompts or post-hoc workspace activity.

## Operating Context

The product runs beside a coding-agent workflow. The dashboard is used to inspect an active session, understand a policy decision, and approve or deny held actions.

## Capabilities and Constraints

- FastAPI policy decision point, PostgreSQL audit store, and React dashboard.
- A local demo harness simulates tool execution; it does not execute shell commands from the dashboard.
- The filesystem watcher remains passive telemetry and cannot inspect this chat's private prompts or internal tools.
- VFB is an optional research reference and is not part of threat detection or enforcement.

## Evidence on Hand

The repository contains a runnable Docker Compose stack and deterministic policy test fixtures. No third-party detection accuracy or security-certification claims are made.

## Product Principles

- Decide before protected actions execute.
- Explain every decision in plain language with stable policy IDs.
- Keep simulations safe and clearly distinguish them from live enforcement.
- Preserve a useful audit trail without exposing secret values.
