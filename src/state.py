"""
Graph state definition for the customer support agent.
"""
# (Docstring: defines the shape of the data passed through the graph.)

from typing import TypedDict, List, Dict, Any
# import typing helpers to define the state dictionary structure

class SupportState(TypedDict, total=False):
    """State that flows through every node of the support graph."""
    # docstring: describes this typed dictionary

    # ── Input ──
    customer_id: str
    # customer's id string

    customer_message: str
    # the text message from the customer

    # ── Classification ──
    category: str
    # assigned category of the ticket

    intent: str
    # identified intent of the customer message

    priority: str
    # priority level of the ticket

    sentiment: str
    # sentiment detected in the message

    classification_confidence: float
    # how confident the classifier is

    classification_rationale: str
    # short explanation for the classification

    # ── Routing ──
    initial_route: str
    # initial routing suggestion (e.g., retrieve or escalate)

    approval_decision: str
    # decision made at the approval gate

    approval_notes: str
    # notes added by human reviewer at approval

    # ── Retrieval ──
    retrieved_docs: List[Dict[str, Any]]
    # knowledge-base articles retrieved for the ticket

    # ── Resolution ──
    draft_response: str
    # draft response from the LLM

    final_response: str
    # final response after any human edits

    resolution_confidence: float
    # confidence of the drafted resolution

    # ── Escalation ──
    needs_escalation: bool
    # whether the ticket must be escalated

    escalation_reason: str
    # reason for escalation

    # ── Bookkeeping ──
    status: str
    # short status string for where the case is in the flow
}],