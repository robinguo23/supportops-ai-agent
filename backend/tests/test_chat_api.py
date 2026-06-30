import app.api.chat as chat_api

from fastapi.testclient import TestClient

from app.db.models import EMBEDDING_DIMENSION
from app.main import app


client = TestClient(app)


def mock_vector_search(
    monkeypatch,
    *,
    document_id: str = "return_policy",
    title: str = "Return Policy",
    content: str = "Customers can return most items within 30 days of delivery.",
    source: str = "return_policy.md",
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
                "distance": 0.25,
                "similarity": 0.75,
            }
        ]

    monkeypatch.setattr(
        chat_api,
        "search_knowledge_chunks_by_embedding",
        fake_search_knowledge_chunks_by_embedding,
    )


def mock_empty_vector_search(monkeypatch):
    monkeypatch.setattr(
        chat_api,
        "generate_query_embedding",
        lambda query: [0.1] * EMBEDDING_DIMENSION,
    )

    def fake_empty_search(
        db,
        query_embedding,
        limit: int = 3,
    ):
        return []

    monkeypatch.setattr(
        chat_api,
        "search_knowledge_chunks_by_embedding",
        fake_empty_search,
    )


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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


def test_unknown_order_creates_ticket():
    response = client.post(
        "/chat",
        json={"message": "Where is my order ORD-9999?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is True
    assert data["tool_used"] == "create_support_ticket"
    assert data["tool_result"]["issue_type"] == "missing_order"
    assert data["tool_result"]["status"] == "open"
    assert "ticket_id" in data["tool_result"]


def test_refund_request_creates_ticket():
    response = client.post(
        "/chat",
        json={"message": "I want a refund."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is True
    assert data["tool_used"] == "create_support_ticket"
    assert data["tool_result"]["issue_type"] == "refund_request"
    assert data["tool_result"]["status"] == "open"
    assert "ticket_id" in data["tool_result"]


def test_normal_message_falls_back_when_no_vector_match(monkeypatch):
    mock_empty_vector_search(monkeypatch)

    response = client.post(
        "/chat",
        json={"message": "Hello there"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["reply"] == "You said: Hello there"


def test_list_tickets_returns_ticket_list():
    response = client.get("/tickets")

    assert response.status_code == 200

    data = response.json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)


def test_update_ticket_status_to_resolved():
    create_response = client.post(
        "/chat",
        json={"message": "I want a refund."},
    )

    assert create_response.status_code == 200

    created_ticket = create_response.json()["tool_result"]
    ticket_id = created_ticket["ticket_id"]

    update_response = client.patch(
        f"/tickets/{ticket_id}/status",
        params={"status": "resolved"},
    )

    assert update_response.status_code == 200

    data = update_response.json()
    assert data["ticket"]["ticket_id"] == ticket_id
    assert data["ticket"]["status"] == "resolved"


def test_chat_uses_vector_search_for_return_policy(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="return_policy",
        title="Return Policy",
        content="Customers can return most items within 30 days of delivery.",
        source="return_policy.md",
    )

    response = client.post(
        "/chat",
        json={"message": "Can I return an item after delivery?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert "sources" in data["tool_result"]
    assert data["tool_result"]["sources"][0]["title"] == "Return Policy"
    assert data["tool_result"]["sources"][0]["similarity"] == 0.75
    assert "30 days" in data["reply"]


def test_chat_uses_vector_search_for_refund_timing_question(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="refund_policy",
        title="Refund Policy",
        content="Refunds are usually processed within 5 to 7 working days.",
        source="refund_policy.md",
    )

    response = client.post(
        "/chat",
        json={"message": "How long does a refund take?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is False
    assert data["tool_used"] == "knowledge_vector_search"
    assert data["tool_result"]["sources"][0]["title"] == "Refund Policy"
    assert "5 to 7 working days" in data["reply"]


def test_refund_request_still_creates_ticket():
    response = client.post(
        "/chat",
        json={"message": "I want a refund."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["needs_human_handoff"] is True
    assert data["tool_used"] == "create_support_ticket"
    assert data["tool_result"]["issue_type"] == "refund_request"


def test_vector_search_endpoint_uses_mocked_embedding(monkeypatch):
    mock_vector_search(
        monkeypatch,
        document_id="delivery_policy",
        title="Delivery Policy",
        content="Standard delivery usually takes 3 to 5 working days.",
        source="delivery_policy.md",
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