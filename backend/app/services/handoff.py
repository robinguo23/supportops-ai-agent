HANDOFF_KEYWORDS = [
    "refund",
    "complaint",
    "angry",
    "human",
    "manager",
    "cancel",
    "charged twice",
    "wrong item",
]


def should_handoff_to_human(message: str) -> bool:
    normalized_message = message.lower()
    return any(keyword in normalized_message for keyword in HANDOFF_KEYWORDS)


def classify_issue_type(message: str) -> str:
    normalized_message = message.lower()

    if "refund" in normalized_message:
        return "refund_request"

    if "complaint" in normalized_message or "angry" in normalized_message:
        return "complaint"

    if "cancel" in normalized_message:
        return "cancellation"

    if "wrong item" in normalized_message:
        return "wrong_item"

    if "charged twice" in normalized_message:
        return "billing_issue"

    if "human" in normalized_message or "manager" in normalized_message:
        return "human_support_request"

    return "general_support"