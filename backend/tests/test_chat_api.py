from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "supportops-ai-agent-backend"


def test_known_order_returns_order_status():
    response = client.post(
        "/chat",
        json={"message": "Where is my order ORD-1001?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "check_order_status"
    assert data["tool_result"]["found"] is True
    assert data["tool_result"]["order_id"] == "ORD-1001"
    assert "shipped" in data["reply"]


def test_unknown_order_creates_support_ticket():
    response = client.post(
        "/chat",
        json={"message": "Where is my order ORD-9999?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is True
    assert data["tool_used"] == "create_support_ticket"
    assert data["tool_result"]["ticket_id"].startswith("TCK-")
    assert data["tool_result"]["issue_type"] == "missing_order"
    assert data["tool_result"]["status"] == "open"


def test_refund_request_creates_support_ticket():
    response = client.post(
        "/chat",
        json={"message": "I want a refund"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is True
    assert data["tool_used"] == "create_support_ticket"
    assert data["tool_result"]["ticket_id"].startswith("TCK-")
    assert data["tool_result"]["issue_type"] == "refund_request"
    assert data["tool_result"]["status"] == "open"


def test_normal_message_does_not_trigger_handoff():
    response = client.post(
        "/chat",
        json={"message": "Hello, how are you?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] is None
    assert data["tool_result"] is None
    assert "You said:" in data["reply"]

def test_list_tickets_returns_ticket_list():
    response = client.get("/tickets")

    assert response.status_code == 200

    data = response.json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)