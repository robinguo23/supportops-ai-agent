from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import SupportTicket


def support_ticket_to_dict(ticket: SupportTicket) -> dict:
    return {
        "ticket_id": ticket.ticket_id,
        "issue_type": ticket.issue_type,
        "summary": ticket.summary,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
    }


def generate_ticket_id(db: Session) -> str:
    latest_id = db.query(func.max(SupportTicket.id)).scalar() or 0
    return f"TCK-{latest_id + 1001}"


def create_support_ticket(db: Session, issue_type: str, summary: str) -> dict:
    ticket = SupportTicket(
        ticket_id=generate_ticket_id(db),
        issue_type=issue_type,
        summary=summary,
        status="open",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return support_ticket_to_dict(ticket)

def list_support_tickets(db: Session, limit: int = 20) -> list[dict]:
    tickets = (
        db.query(SupportTicket)
        .order_by(SupportTicket.id.desc())
        .limit(limit)
        .all()
    )

    return [support_ticket_to_dict(ticket) for ticket in tickets]

def update_support_ticket_status(
    db: Session,
    ticket_id: str,
    status: str,
) -> dict | None:
    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.ticket_id == ticket_id)
        .first()
    )

    if ticket is None:
        return None

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return support_ticket_to_dict(ticket)