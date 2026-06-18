from datetime import datetime, timezone


MOCK_TICKETS: list[dict] = []


def create_support_ticket(issue_type: str, summary: str) -> dict:
    ticket_id = f"TCK-{len(MOCK_TICKETS) + 1001}"

    ticket = {
        "ticket_id": ticket_id,
        "issue_type": issue_type,
        "summary": summary,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    MOCK_TICKETS.append(ticket)

    return ticket