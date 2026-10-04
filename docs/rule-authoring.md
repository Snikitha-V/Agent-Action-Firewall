# Rule Authoring

Rules must be deterministic, explainable, and versioned. Each rule needs a stable ID, plain-language rationale, numeric score, positive fixtures, false-positive fixtures, owner, and `last_reviewed` date.

Do not add broad keyword rules without tests. Prefer combinations of action type, target, requested scope, and causal history. A rule change requires a changelog entry and an update to the threat model where it changes risk coverage.
