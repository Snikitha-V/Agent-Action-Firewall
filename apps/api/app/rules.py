from dataclasses import dataclass
import re

from .schemas import EventIn


@dataclass(frozen=True)
class Rule:
    rule_id: str
    label: str
    score: int
    explanation: str
    terms: tuple[str, ...] = ()


RULES = (
    Rule("TM-101", "Instruction override attempt", 35, "The request attempts to override established safety or operating constraints.", ("ignore previous", "system prompt", "bypass safety", "jailbreak")),
    Rule("TM-201", "Sensitive material access", 65, "The action targets environment configuration, credentials, or private keys.", (".env", "printenv", "aws_secret", "api_key", "id_rsa", "credentials", ".ssh/")),
    Rule("TM-301", "Destructive command", 80, "The proposed command can irreversibly remove data or rewrite shared history.", ("rm -rf", "drop database", "git push --force", "chmod -r", "mkfs")),
    Rule("TM-401", "External data transfer", 30, "The action sends data to an external network destination and requires review.", ("curl ", "wget ", "nc ", "http://", "https://", "upload")),
    Rule("TM-501", "Dependency supply-chain change", 30, "The action installs a package or changes a dependency source.", ("npm install", "pip install", "curl | sh", "registry=")),
    Rule("TM-601", "Protected source change", 55, "The action writes to a protected configuration or CI path.", (".github/workflows", "docker-compose.yml", "pyproject.toml", "package.json")),
)


def evaluate(event: EventIn) -> tuple[float, str, list[dict]]:
    request_context = " ".join((event.user_request, event.agent_intent)).lower()
    action_context = " ".join((event.agent_intent, event.target)).lower()
    target_context = event.target.lower()

    def matches(rule: Rule) -> bool:
        if rule.rule_id == "TM-101":
            return any(term in request_context for term in rule.terms)
        if rule.rule_id in {"TM-201", "TM-401"}:
            return any(term in action_context for term in rule.terms)
        return any(term in target_context for term in rule.terms)

    evidence = [
        {"rule_id": rule.rule_id, "label": rule.label, "score": rule.score, "explanation": rule.explanation}
        for rule in RULES if matches(rule)
    ]
    rule_ids = {item["rule_id"] for item in evidence}
    if {"TM-201", "TM-401"}.issubset(rule_ids):
        evidence.append({"rule_id": "TM-402", "label": "Credential exfiltration chain", "score": 40, "explanation": "Sensitive material access is combined with an external transfer path."})
    if event.action_type == "file_write" and re.search(r"(^|/)(\.env|\.github|infra|deploy)(/|$)", event.target.lower()):
        evidence.append({"rule_id": "TM-602", "label": "Protected path write", "score": 55, "explanation": "The proposed write targets a protected configuration or deployment path."})
    score = min(100, sum(item["score"] for item in evidence))
    decision = "hold" if score >= 50 else "review" if score >= 30 else "allow"
    return score, decision, evidence
