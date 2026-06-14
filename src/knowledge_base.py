"""
Knowledge base articles and simple keyword-based retriever.
"""

from typing import List, Dict, Any

KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "kb_001",
        "category": "billing",
        "title": "Refund policy",
        "content": (
            "Customers can request a refund within 7 days of purchase for duplicate charges "
            "or accidental purchases. Refunds for subscription renewals require account verification."
        ),
    },
    {
        "id": "kb_002",
        "category": "billing",
        "title": "Invoice and payment issues",
        "content": (
            "If a payment fails, ask the customer to verify card details, billing address, "
            "and available balance. Escalate repeated charge failures after 2 attempts."
        ),
    },
    {
        "id": "kb_003",
        "category": "technical",
        "title": "App crashes on login",
        "content": (
            "If the app crashes on login, ask the user to clear cache, update to the latest version, "
            "restart the device, and try again. Escalate if crash logs are available or issue persists."
        ),
    },
    {
        "id": "kb_004",
        "category": "technical",
        "title": "Password reset troubleshooting",
        "content": (
            "If password reset email is not received, ask the customer to check spam, confirm the email address, "
            "and retry after 5 minutes. Escalate if the account is locked."
        ),
    },
    {
        "id": "kb_005",
        "category": "order",
        "title": "Order status policy",
        "content": (
            "If an order is marked shipped, provide the tracking window of 24 hours. "
            "If tracking is unavailable after 24 hours, escalate to logistics support."
        ),
    },
    {
        "id": "kb_006",
        "category": "account",
        "title": "Account locked procedure",
        "content": (
            "For locked accounts, verify the registered email, last successful login, and customer ID. "
            "Do not unlock manually without verification. Route high-risk account access issues for review."
        ),
    },
]


def simple_retrieve(query: str, category: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Score knowledge-base articles by category match + keyword overlap,
    then return the top-k results.
    """
    query_words = set(query.lower().split())
    scored = []

    for doc in KNOWLEDGE_BASE:
        score = 0
        if doc["category"] == category:
            score += 3

        content_words = set((doc["title"] + " " + doc["content"]).lower().split())
        overlap = len(query_words.intersection(content_words))
        score += overlap

        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    docs = [doc for score, doc in scored if score > 0][:top_k]
    return docs
