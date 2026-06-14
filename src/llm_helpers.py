"""
LLM helper functions for ticket classification and resolution drafting.
"""

from src.config import llm
from src.models import TicketClassification, ResolutionDecision
from src.state import SupportState

# ── Structured-output wrappers ──
classifier = llm.with_structured_output(TicketClassification)
resolver = llm.with_structured_output(ResolutionDecision)


def classify_with_llm(customer_message: str) -> TicketClassification:
    """Classify a customer message into category, intent, priority, etc."""
    prompt = f"""
You are a customer support ticket classifier.

Read the ticket and classify:
- category
- intent
- priority
- sentiment
- confidence
- rationale

Ticket:
{customer_message}
"""
    return classifier.invoke(prompt)


def resolve_with_llm(state: SupportState) -> ResolutionDecision:
    """Draft a resolution response using the ticket context and retrieved knowledge."""
    kb_text = "\n\n".join(
        [
            f"[{doc['id']}] {doc['title']}\nCategory: {doc['category']}\n{doc['content']}"
            for doc in state.get("retrieved_docs", [])
        ]
    )

    prompt = f"""
You are a customer support resolution assistant.

Use the ticket classification, customer message, and retrieved knowledge
to draft a helpful and safe support response.

Rules:
- If the issue involves security risk, missing verification, locked account, legal risk,
  or insufficient information, set needs_escalation=true.
- Keep the response clear, polite, and actionable.
- Do not invent policy beyond the knowledge provided.

Customer ID: {state.get('customer_id', '')}
Message: {state.get('customer_message', '')}
Category: {state.get('category', '')}
Intent: {state.get('intent', '')}
Priority: {state.get('priority', '')}
Sentiment: {state.get('sentiment', '')}
Approval notes: {state.get('approval_notes', '')}

Retrieved Knowledge:
{kb_text if kb_text else "No relevant knowledge found."}
"""
    return resolver.invoke(prompt)
