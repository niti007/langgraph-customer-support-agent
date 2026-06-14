"""
Graph node functions and routing helpers.
"""

from langgraph.types import interrupt

from src.state import SupportState
from src.knowledge_base import simple_retrieve
from src.llm_helpers import classify_with_llm, resolve_with_llm


# ─────────────────────────────────────────────
# Node: classify_ticket
# ─────────────────────────────────────────────
def classify_ticket(state: SupportState) -> SupportState:
    """Classify the incoming customer message using the LLM."""
    result = classify_with_llm(state["customer_message"])

    # Determine initial routing hint
    routable_intents = {
        "refund_request",
        "payment_issue",
        "bug_report",
        "password_reset",
        "order_status",
        "account_access",
        "general_question",
    }
    initial_route = "retrieve" if result.intent in routable_intents else "escalate"

    return {
        "category": result.category,
        "intent": result.intent,
        "priority": result.priority,
        "sentiment": result.sentiment,
        "classification_confidence": result.confidence,
        "classification_rationale": result.rationale,
        "initial_route": initial_route,
        "status": "classified",
    }


# ─────────────────────────────────────────────
# Node: approval_gate  (human-in-the-loop #1)
# ─────────────────────────────────────────────
def approval_gate(state: SupportState) -> SupportState:
    """
    Gate that pauses execution for human review when the ticket is
    high-risk (high/urgent priority, low confidence, or sensitive category).
    """
    needs_human_gate = (
        state.get("priority") in ["high", "urgent"]
        or state.get("classification_confidence", 0) < 0.70
        or state.get("category") in ["billing", "account"]
    )

    if not needs_human_gate:
        return {
            "approval_decision": "approved",
            "approval_notes": "Auto-approved: low-risk case",
            "status": "routing_approved",
        }

    human_input = interrupt(
        {
            "stage": "classification_review",
            "message": "Review ticket classification and approve routing.",
            "ticket": state["customer_message"],
            "classification": {
                "category": state.get("category"),
                "intent": state.get("intent"),
                "priority": state.get("priority"),
                "sentiment": state.get("sentiment"),
                "confidence": state.get("classification_confidence"),
                "rationale": state.get("classification_rationale"),
                "proposed_route": state.get("initial_route"),
            },
            "expected_reply_format": {
                "decision": "approved | escalate",
                "notes": "optional reviewer notes",
            },
        }
    )

    if isinstance(human_input, dict):
        decision = human_input.get("decision", "approved")
        notes = human_input.get("notes", "")
    else:
        decision = str(human_input)
        notes = ""

    return {
        "approval_decision": decision,
        "approval_notes": notes,
        "status": "routing_reviewed",
    }


# ─────────────────────────────────────────────
# Routing: after approval gate
# ─────────────────────────────────────────────
def route_after_approval(state: SupportState) -> str:
    """Decide the next node after the approval gate."""
    if state.get("approval_decision") == "escalate":
        return "escalate_case"
    if state.get("initial_route") == "retrieve":
        return "retrieve_knowledge"
    return "escalate_case"


# ─────────────────────────────────────────────
# Node: retrieve_knowledge
# ─────────────────────────────────────────────
def retrieve_knowledge(state: SupportState) -> SupportState:
    """Fetch relevant knowledge-base articles for the ticket."""
    docs = simple_retrieve(
        query=state["customer_message"],
        category=state.get("category", "general"),
        top_k=3,
    )
    return {
        "retrieved_docs": docs,
        "status": "knowledge_retrieved",
    }


# ─────────────────────────────────────────────
# Node: draft_resolution
# ─────────────────────────────────────────────
def draft_resolution(state: SupportState) -> SupportState:
    """Use the LLM to draft a customer response."""
    decision = resolve_with_llm(state)
    return {
        "draft_response": decision.draft_response,
        "needs_escalation": decision.needs_escalation,
        "escalation_reason": decision.escalation_reason,
        "resolution_confidence": decision.confidence,
        "status": "draft_ready",
    }


# ─────────────────────────────────────────────
# Node: final_review_gate  (human-in-the-loop #2)
# ─────────────────────────────────────────────
def final_review_gate(state: SupportState) -> SupportState:
    """
    Gate that pauses for human review of the drafted response
    when escalation is flagged, confidence is low, or the ticket is sensitive.
    """
    must_review = (
        state.get("needs_escalation", False)
        or state.get("resolution_confidence", 0) < 0.80
        or state.get("priority") in ["high", "urgent"]
        or state.get("category") in ["billing", "account"]
    )

    if not must_review:
        return {
            "final_response": state.get("draft_response", ""),
            "status": "approved_final_response",
        }

    human_input = interrupt(
        {
            "stage": "final_response_review",
            "message": "Approve, edit, or escalate the drafted response.",
            "draft_response": state.get("draft_response"),
            "needs_escalation": state.get("needs_escalation"),
            "escalation_reason": state.get("escalation_reason"),
            "confidence": state.get("resolution_confidence"),
            "expected_reply_format": {
                "decision": "approve | edit | escalate",
                "edited_response": "required only if decision=edit",
                "notes": "optional reviewer notes",
            },
        }
    )

    if not isinstance(human_input, dict):
        human_input = {"decision": str(human_input)}

    decision = human_input.get("decision", "approve")
    notes = human_input.get("notes", "")

    if decision == "edit":
        return {
            "final_response": human_input.get(
                "edited_response", state.get("draft_response", "")
            ),
            "approval_notes": (
                state.get("approval_notes", "")
                + f" | final review notes: {notes}"
            ).strip(),
            "needs_escalation": False,
            "status": "approved_final_response",
        }

    if decision == "escalate":
        return {
            "needs_escalation": True,
            "escalation_reason": notes
            or state.get("escalation_reason", "Human reviewer requested escalation"),
            "status": "review_requested_escalation",
        }

    # Default: approve
    return {
        "final_response": state.get("draft_response", ""),
        "approval_notes": (
            state.get("approval_notes", "") + f" | final review notes: {notes}"
        ).strip(),
        "status": "approved_final_response",
    }


# ─────────────────────────────────────────────
# Routing: after final review
# ─────────────────────────────────────────────
def route_resolution_or_escalation(state: SupportState) -> str:
    """Route to resolve or escalate based on final review outcome."""
    if state.get("needs_escalation", False):
        return "escalate_case"
    return "resolve_case"


# ─────────────────────────────────────────────
# Node: resolve_case
# ─────────────────────────────────────────────
def resolve_case(state: SupportState) -> SupportState:
    """Finalize the case as resolved."""
    return {
        "status": "resolved",
        "final_response": state.get("final_response", state.get("draft_response", "")),
    }


# ─────────────────────────────────────────────
# Node: escalate_case
# ─────────────────────────────────────────────
def escalate_case(state: SupportState) -> SupportState:
    """Escalate the case to a human support specialist."""
    escalation_msg = (
        "Your case has been escalated to a human support specialist. "
        f"Reason: {state.get('escalation_reason', 'Needs manual review')}."
    )
    return {
        "status": "escalated",
        "final_response": escalation_msg,
    }
