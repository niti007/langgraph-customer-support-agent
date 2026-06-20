"""
LLM helper functions for ticket classification and resolution drafting.
"""
# (Docstring: helpers that call the LLM for tasks.)

from src.config import llm
# import the shared llm client from config

from src.models import TicketClassification, ResolutionDecision
# import the pydantic models that define expected structured outputs

from src.state import SupportState
# import the SupportState typing for hints (not strictly required at runtime)

# ── Structured-output wrappers ──
classifier = llm.with_structured_output(TicketClassification)
# create a wrapper around the llm that will parse outputs into TicketClassification

resolver = llm.with_structured_output(ResolutionDecision)
# create a wrapper that will parse outputs into ResolutionDecision

def classify_with_llm(customer_message: str) -> TicketClassification:
    """Classify a customer message into category, intent, priority, etc."""
    # function docstring: describes purpose

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
    # build the prompt that will be sent to the LLM, including the ticket text

    return classifier.invoke(prompt)
    # call the classifier wrapper and return the structured result

def resolve_with_llm(state: SupportState) -> ResolutionDecision:
    """Draft a resolution response using the ticket context and retrieved knowledge."""
    # function docstring: explains we use ticket + KB to draft a response

    kb_text = "\n\n".join(
        [
            f"[{doc['id']}] {doc['title']}\nCategory: {doc['category']}\n{doc['content']}"
            for doc in state.get("retrieved_docs", [])
        ]
    )
    # format retrieved knowledge documents into a readable block; if none, will be empty

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
    # build a prompt that provides the LLM with the ticket, classification, notes, and KB

    return resolver.invoke(prompt)
    # call the resolver wrapper and return the structured resolution decision
