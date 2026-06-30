import app.api.chat as chat_api

from fastapi.testclient import TestClient

from app.db.models import EMBEDDING_DIMENSION
from app.main import app


client = TestClient(app)


def mock_vector_search(
    monkeypatch,
    *,
    document_id: str = "refund_request_policy",
    title: str = "Refund Request Policy",
    content: str = (
        "If a customer wants to request a refund, they should provide "
        "their order ID and explain the reason for the refund request."
    ),
    source: str = "refund_request_policy.md",
    similarity: float = 0.78,
):
    monkeypatch.setattr(
        chat_api,
        "generate_query_embedding",
        lambda query: [0.1] * EMBEDDING_DIMENSION,
    )

    def fake_search_knowledge_chunks_by_embedding(
        db,
        query_embedding,
        limit: int = 3,
    ):
        return [
            {
                "id": 1,
                "document_id": document_id,
                "title": title,
                "content": content,
                "source": source,
                "distance": 1 - similarity,
                "similarity": similarity,
            }
        ]

    monkeypatch.setattr(
        chat_api,
        "search_knowledge_chunks_by_embedding",
        fake_search_knowledge_chunks_by_embedding,
    )


def mock_low_similarity_vector_search(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="delivery_policy",
        title="Delivery Policy",
        content="Standard delivery usually takes 3 to 5 working days.",
        source="delivery_policy.md",
        similarity=0.45,
    )


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_known_order_returns_status_and_asks_feedback():
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
    assert data["tool_result"]["conversation_action"] == "ask_resolution_feedback"


def test_unknown_order_asks_escalation_but_does_not_create_ticket():
    response = client.post(
        "/chat",
        json={"message": "Where is my order ORD-9999?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "order_not_found"
    assert data["tool_result"]["reason"] == "order_not_found"
    assert data["tool_result"]["conversation_action"] == "ask_escalation"
    assert "ticket_id" not in data["tool_result"]


def test_out_of_scope_question_does_not_create_ticket():
    response = client.post(
        "/chat",
        json={"message": "What is the weather today?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "out_of_scope_guardrail"
    assert data["tool_result"]["reason"] == "out_of_scope"
    assert data["tool_result"]["conversation_action"] == "allow_new_question"
    assert "ticket_id" not in data["tool_result"]


def test_refund_request_uses_rag_and_does_not_create_ticket(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="refund_request_policy",
        title="Refund Request Policy",
        content=(
            "If a customer wants to request a refund, they should provide "
            "their order ID and explain the reason for the refund request."
        ),
        source="refund_request_policy.md",
        similarity=0.82,
    )

    response = client.post(
        "/chat",
        json={"message": "I want a refund."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert data["tool_result"]["conversation_action"] == "ask_resolution_feedback"
    assert data["tool_result"]["sources"][0]["title"] == "Refund Request Policy"
    assert "ticket_id" not in data["tool_result"]
    assert "refund" in data["reply"].lower()


def test_damaged_item_uses_rag_and_does_not_create_ticket(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="damaged_items_policy",
        title="Damaged Items Policy",
        content=(
            "If an item arrives damaged, faulty, broken, or defective, "
            "the customer should provide their order ID, a description, and a photo."
        ),
        source="damaged_items_policy.md",
        similarity=0.80,
    )

    response = client.post(
        "/chat",
        json={"message": "My item arrived damaged."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert data["tool_result"]["conversation_action"] == "ask_resolution_feedback"
    assert data["tool_result"]["sources"][0]["title"] == "Damaged Items Policy"
    assert "ticket_id" not in data["tool_result"]


def test_billing_issue_uses_rag_and_does_not_create_ticket(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="billing_policy",
        title="Billing Policy",
        content=(
            "If a customer believes they were charged twice, they should check "
            "whether one charge is pending and provide payment details if both charges completed."
        ),
        source="billing_policy.md",
        similarity=0.79,
    )

    response = client.post(
        "/chat",
        json={"message": "I was charged twice."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert data["tool_result"]["conversation_action"] == "ask_resolution_feedback"
    assert data["tool_result"]["sources"][0]["title"] == "Billing Policy"
    assert "ticket_id" not in data["tool_result"]


def test_low_similarity_support_question_asks_escalation(monkeypatch):
    mock_low_similarity_vector_search(monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "My refund situation is unusual and confusing."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert data["tool_result"]["reason"] == "top_similarity_below_threshold"
    assert data["tool_result"]["conversation_action"] == "ask_escalation"
    assert "ticket_id" not in data["tool_result"]


def test_escalation_endpoint_creates_ticket():
    response = client.post(
        "/tickets/escalate",
        json={
            "original_question": "I want a refund.",
            "reason": "user_requested_human_support",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "ticket" in data
    assert data["reason"] == "user_requested_human_support"
    assert data["ticket"]["issue_type"] == "human_escalation"
    assert data["ticket"]["status"] == "open"
    assert "ticket_id" in data["ticket"]


def test_list_tickets_returns_ticket_list():
    response = client.get("/tickets")

    assert response.status_code == 200

    data = response.json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)


def test_update_ticket_status_to_resolved():
    create_response = client.post(
        "/tickets/escalate",
        json={
            "original_question": "I need human support.",
            "reason": "user_requested_human_support",
        },
    )

    assert create_response.status_code == 200

    created_ticket = create_response.json()["ticket"]
    ticket_id = created_ticket["ticket_id"]

    update_response = client.patch(
        f"/tickets/{ticket_id}/status",
        params={"status": "resolved"},
    )

    assert update_response.status_code == 200

    data = update_response.json()
    assert data["ticket"]["ticket_id"] == ticket_id
    assert data["ticket"]["status"] == "resolved"


def test_vector_search_endpoint_uses_mocked_embedding(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="delivery_policy",
        title="Delivery Policy",
        content="Standard delivery usually takes 3 to 5 working days.",
        source="delivery_policy.md",
        similarity=0.75,
    )

    response = client.get(
        "/knowledge/vector-search",
        params={"query": "My parcel is late"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "My parcel is late"
    assert data["count"] == 1
    assert data["chunks"][0]["title"] == "Delivery Policy"
    assert data["chunks"][0]["similarity"] == 0.75