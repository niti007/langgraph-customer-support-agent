"""
Graph state definition for the customer support agent.
"""

from typing import TypedDict, List, Dict, Any


class SupportState(TypedDict, total=False):
    """State that flows through every node of the support graph."""

    # ── Input ──
    customer_id: str
    customer_message: str

    # ── Classification ──
    category: str
    intent: str
    priority: str
    sentiment: str
    classification_confidence: float
    classification_rationale: str

    # ── Routing ──
    initial_route: str
    approval_decision: str
    approval_notes: str

    # ── Retrieval ──
    retrieved_docs: List[Dict[str, Any]]

    # ── Resolution ──
    draft_response: str
    final_response: str
    resolution_confidence: float

    # ── Escalation ──
    needs_escalation: bool
    escalation_reason: str

    # ── Bookkeeping ──
    status: str
