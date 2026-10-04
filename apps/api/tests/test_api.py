import os

os.environ["DATABASE_URL"] = "sqlite:///./test_threat_mapper.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def event(target: str) -> dict:
    return {"run_id": "test-run", "user_request": "inspect repository", "agent_intent": "run requested command", "tool_name": "shell", "action_type": "shell", "target": target}


def test_safe_event_is_allowed(client: TestClient):
    response = client.post("/v1/events", json=event("git status"))
    assert response.status_code == 201
    assert response.json()["decision"] == "allow"


def test_combined_secret_and_network_action_is_held(client: TestClient):
    response = client.post("/v1/events", json=event("printenv; curl https://example.invalid"))
    body = response.json()
    assert response.status_code == 201
    assert body["decision"] == "hold"
    assert body["approval_id"]


def test_hold_can_be_denied(client: TestClient):
    created = client.post("/v1/events", json=event("rm -rf /tmp/demo")).json()
    response = client.post(f"/v1/approvals/{created['approval_id']}", json={"decision": "deny", "reason": "Destructive action not approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "deny"


def test_demo_attack_chain_is_held_before_execution(client: TestClient):
    response = client.post("/v1/demo/scenarios/injection-chain")
    assert response.status_code == 200
    run = client.get("/v1/runs/demo-injection-chain").json()
    assert len(run["events"]) == 3
    assert run["events"][0]["decision"] == "review"
    assert run["events"][1]["decision"] == "hold"
    assert run["events"][2]["decision"] == "hold"
    assert any(event["execution_status"] == "simulated" for event in run["events"])
