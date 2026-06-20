"""
Graph node functions and routing helpers.
"""
# (Docstring: contains the functions that run at each node of the graph.)

from langgraph.types import interrupt
# import 'interrupt' which pauses the graph to ask for human input

from src.state import SupportState
# import the SupportState typing to annotate state parameters

from src.knowledge_base import simple_retrieve
# import the simple KB retriever function

from src.llm_helpers import classify_with_llm, resolve_with_llm
# import functions that call the LLM to classify and draft resolutions

# ─────────────────────────────────────────────
# Node: classify_ticket
# ─────────────────────────────────────────────
def classify_ticket(state: SupportState) -> SupportState:
    """Classify the incoming customer message using the LLM."""
    # function docstring: uses LLM to classify the ticket

    result = classify_with_llm(state["customer_message"])
    # call the classifier with the customer's message and store the structured result

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
    # set of intents that we can handle automatically (i.e., route to retrieval)

    initial_route = "retrieve" if result.intent in routable_intents else "escalate"
    # if the intent is in the known set, plan to retrieve KB; otherwise plan to escalate

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
    # return an updated state dictionary with classification results and a routing hint

# ─────────────────────────────────────────────
# Node: approval_gate  (human-in-the-loop #1)
# ─────────────────────────────────────────────
def approval_gate(state: SupportState) -> SupportState:
    """
    Gate that pauses execution for human review when the ticket is
    high-risk (high/urgent priority, low confidence, or sensitive category).
    """
    # docstring: explains conditions when human review is needed

    needs_human_gate = (
        state.get("priority") in ["high", "urgent"]
        or state.get("classification_confidence", 0) < 0.70
        or state.get("category") in ["billing", "account"]
    )
    # determine if the ticket should be reviewed by a human:
    # if priority is high/urgent, confidence is low, or category is sensitive

    if not needs_human_gate:
        return {
            "approval_decision": "approved",
            "approval_notes": "Auto-approved: low-risk case",
            "status": "routing_approved",
        }
    # if no human gate needed, auto-approve and return updated state

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
            },
            "expected_reply_format": {
                "decision": "approved | escalate",
                "notes": "optional reviewer notes",
            },
        }
    )
    # pause the graph and ask a human to review classification; provide expected reply format

    if isinstance(human_input, dict):
        decision = human_input.get("decision", "approved")
        notes = human_input.get("notes", "")
    else:
        decision = str(human_input)
        notes = ""
    # handle either structured (dict) or simple string response from the human

    return {
        "approval_decision": decision,
        "approval_notes": notes,
        "status": "routing_reviewed",
    }
    # return the human's decision and notes in the state

# ─────────────────────────────────────────────
# Routing: after approval gate
# ─────────────────────────────────────────────
def route_after_approval(state: SupportState) -> str:
    """Decide the next node after the approval gate."""
    # docstring: picks which node to go to next

    if state.get("approval_decision") == "escalate":
        return "escalate_case"
    # if human said escalate, go to escalation

    if state.get("initial_route") == "retrieve":
        return "retrieve_knowledge"
    # if initial routing suggested retrieval, go retrieve knowledge

    return "escalate_case"
    # default to escalation if no other conditions met

# ─────────────────────────────────────────────
# Node: retrieve_knowledge
# ─────────────────────────────────────────────
def retrieve_knowledge(state: SupportState) -> SupportState:
    """Fetch relevant knowledge-base articles for the ticket."""
    # function docstring: gets KB articles relevant to the ticket

    docs = simple_retrieve(
        query=state["customer_message"],
        category=state.get("category", "general"),
        top_k=3,
    )
    # call the simple retriever with the message and category, ask for top 3

    return {
        "retrieved_docs": docs,
        "status": "knowledge_retrieved",
    }
    # put the retrieved docs into state and mark status

# ─────────────────────────────────────────────
# Node: draft_resolution
# ─────────────────────────────────────────────
def draft_resolution(state: SupportState) -> SupportState:
    """Use the LLM to draft a customer response."""
    # docstring: asks LLM to draft the response

    decision = resolve_with_llm(state)
    # call the resolver that returns a structured ResolutionDecision

    return {
        "draft_response": decision.draft_response,
        "needs_escalation": decision.needs_escalation,
        "escalation_reason": decision.escalation_reason,
        "resolution_confidence": decision.confidence,
        "status": "draft_ready",
    }
    # store the LLM's draft and flags in the state

# ─────────────────────────────────────────────
# Node: final_review_gate  (human-in-the-loop #2)
# ─────────────────────────────────────────────
def final_review_gate(state: SupportState) -> SupportState:
    """
    Gate that pauses for human review of the drafted response
    when escalation is flagged, confidence is low, or the ticket is sensitive.
    """
    # docstring: explains when to require final human review

    must_review = (
        state.get("needs_escalation", False)
        or state.get("resolution_confidence", 0) < 0.80
        or state.get("priority") in ["high", "urgent"]
        or state.get("category") in ["billing", "account"]
    )
    # decide if final human review is required based on flags or low confidence

    if not must_review:
        return {
            "final_response": state.get("draft_response", ""),
            "status": "approved_final_response",
        }
    # if no review needed, finalize the draft as the final response

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
    # pause the graph and ask a human to approve/edit/escalate the draft

    if not isinstance(human_input, dict):
        human_input = {"decision": str(human_input)}
    # if the human reply is not a dict, convert it to a simple dict with a decision

    decision = human_input.get("decision", "approve")
    notes = human_input.get("notes", "")
    # extract decision and notes from the human input

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
    # if the reviewer edited, use the edited response, append review notes, and mark approved

    if decision == "escalate":
        return {
            "needs_escalation": True,
            "escalation_reason": notes
            or state.get("escalation_reason", "Human reviewer requested escalation"),
            "status": "review_requested_escalation",
        }
    # if the reviewer chose to escalate, set escalation flags and reason

    # Default: approve
    return {
        "final_response": state.get("draft_response", ""),
        "approval_notes": (
            state.get("approval_notes", "") + f" | final review notes: {notes}"
        ).strip(),
        "status": "approved_final_response",
    }
    # otherwise, treat it as approved and attach any notes

# ─────────────────────────────────────────────
# Routing: after final review
# ─────────────────────────────────────────────
def route_resolution_or_escalation(state: SupportState) -> str:
    """Route to resolve or escalate based on final review outcome."""
    # docstring: decide final routing after review

    if state.get("needs_escalation", False):
        return "escalate_case"
    # if escalation needed, go escalate

    return "resolve_case"
    # otherwise, resolve

# ─────────────────────────────────────────────
# Node: resolve_case
# ─────────────────────────────────────────────
def resolve_case(state: SupportState) -> SupportState:
    """Finalize the case as resolved."""
    # docstring: mark the ticket resolved

    return {
        "status": "resolved",
        "final_response": state.get("final_response", state.get("draft_response", "")),
    }
    # set status to resolved and set final_response from final_response or draft

# ─────────────────────────────────────────────
# Node: escalate_case
# ─────────────────────────────────────────────
def escalate_case(state: SupportState) -> SupportState:
    """Escalate the case to a human support specialist."""
    # docstring: create an escalation message for the user

    escalation_msg = (
        "Your case has been escalated to a human support specialist. "
        f"Reason: {state.get('escalation_reason', 'Needs manual review')}."
    )
    # build a friendly escalation message including the reason

    return {
        "status": "escalated",
        "final_response": escalation_msg,
    }
    # mark the state as escalated and include the escalation message
