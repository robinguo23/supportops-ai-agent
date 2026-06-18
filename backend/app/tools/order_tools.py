import re

from app.data.mock_data import MOCK_ORDERS


def extract_order_id(message: str) -> str | None:
    match = re.search(r"ORD-\d{4}", message.upper())

    if match:
        return match.group(0)

    return None


def check_order_status(order_id: str) -> dict:
    order = MOCK_ORDERS.get(order_id)

    if order is None:
        return {
            "found": False,
            "order_id": order_id,
        }

    return {
        "found": True,
        "order_id": order_id,
        **order,
    }