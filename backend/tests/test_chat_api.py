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

def test_update_ticket_status_to_resolved():
    create_response = client.post(
        "/chat",
        json={"message": "I want a refund"},
    )

    assert create_response.status_code == 200

    created_data = create_response.json()
    ticket_id = created_data["tool_result"]["ticket_id"]

    update_response = client.patch(
        f"/tickets/{ticket_id}/status",
        params={"status": "resolved"},
    )

    assert update_response.status_code == 200

    updated_data = update_response.json()
    assert updated_data["ticket"]["ticket_id"] == ticket_id
    assert updated_data["ticket"]["status"] == "resolved"

def test_return_policy_uses_knowledge_base_search():
    response = client.post(
        "/chat",
        json={"message": "What is your return policy?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_base_search"
    assert data["tool_result"]["article_id"] == "return_policy"
    assert "30 days" in data["reply"]


def test_delivery_question_uses_knowledge_base_search():
    response = client.post(
        "/chat",
        json={"message": "How long does delivery take?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_base_search"
    assert data["tool_result"]["article_id"] == "delivery_time"

def test_search_knowledge_chunks_returns_matches():
    response = client.get(
        "/knowledge/search",
        params={"query": "refund"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "refund"
    assert data["count"] > 0
    assert len(data["chunks"]) > 0
    assert "refund" in data["chunks"][0]["content"].lower()


def test_search_knowledge_chunks_returns_empty_for_unknown_query():
    response = client.get(
        "/knowledge/search",
        params={"query": "zzzzunknownterm"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "zzzzunknownterm"
    assert data["count"] == 0
    assert data["chunks"] == []