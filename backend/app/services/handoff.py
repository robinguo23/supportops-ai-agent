QUESTION_PREFIXES = (
    "what ",
    "what's ",
    "how ",
    "how long ",
    "when ",
    "where ",
    "do you ",
    "does ",
    "can i ",
    "could i ",
    "is it ",
    "are ",
)

POLICY_TERMS = (
    "policy",
    "refund",
    "return",
    "delivery",
    "shipping",
    "take",
    "takes",
    "long",
    "process",
    "processed",
    "allowed",
    "eligible",
    "damaged",
    "faulty",
)

HANDOFF_PHRASES = (
    "i want a refund",
    "i need a refund",
    "i would like a refund",
    "request a refund",
    "refund my order",
    "give me a refund",
    "money back",
    "complaint",
    "angry",
    "human",
    "manager",
    "cancel",
    "charged twice",
    "wrong item",
    "missing order",
    "lost parcel",
    "item arrived damaged",
    "arrived damaged",
    "broken item",
    "faulty item",
)


def normalize_message(message: str) -> str:
    return " ".join(message.lower().strip().split())


def is_informational_policy_question(message: str) -> bool:
    normalized_message = normalize_message(message)

    starts_like_question = any(
        normalized_message.startswith(prefix)
        for prefix in QUESTION_PREFIXES
    )

    contains_policy_term = any(
        term in normalized_message
        for term in POLICY_TERMS
    )

    return starts_like_question and contains_policy_term


def should_handoff_to_human(message: str) -> bool:
    normalized_message = normalize_message(message)

    if is_informational_policy_question(normalized_message):
        return False

    return any(
        phrase in normalized_message
        for phrase in HANDOFF_PHRASES
    )


def classify_issue_type(message: str) -> str:
    normalized_message = normalize_message(message)

    if "refund" in normalized_message or "money back" in normalized_message:
        return "refund_request"

    if "cancel" in normalized_message:
        return "cancellation_request"

    if "charged twice" in normalized_message:
        return "billing_issue"

    if "wrong item" in normalized_message:
        return "wrong_item"

    if (
        "damaged" in normalized_message
        or "broken" in normalized_message
        or "faulty" in normalized_message
    ):
        return "damaged_item"

    if "missing order" in normalized_message or "lost parcel" in normalized_message:
        return "missing_order"

    return "general_support"