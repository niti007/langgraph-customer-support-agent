"""
Pydantic models for structured LLM outputs.
"""
# (Docstring: defines structured output shapes.)

from typing import Literal
# import Literal to define fields that can only be specific strings

from pydantic import BaseModel, Field
# import Pydantic base class and Field helper for descriptions

class TicketClassification(BaseModel):
    """Structured classification of a customer support ticket."""
    # model docstring: describes intent of the model

    category: Literal["billing", "technical", "order", "account", "general"] = Field(
        description="Main category of the support ticket"
    )
    # category must be one of the listed strings; Field adds a description

    intent: Literal[
        "refund_request",
        "payment_issue",
        "bug_report",
        "password_reset",
        "order_status",
        "account_access",
        "complaint",
        "general_question",
        "other",
    ] = Field(description="Customer intent")
    # intent must be one of these specific intents; helps structure LLM output

    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Urgency of the ticket"
    )
    # priority is restricted to these values

    sentiment: Literal["positive", "neutral", "negative", "frustrated"] = Field(
        description="Customer sentiment"
    )
    # sentiment is restricted to these values

    confidence: float = Field(description="Confidence from 0 to 1")
    # confidence is a float indicating how sure the model is

    rationale: str = Field(description="Short explanation")
    # rationale is a short text explaining the classification

class ResolutionDecision(BaseModel):
    """Structured resolution drafted by the LLM."""
    # model docstring: describes purpose

    draft_response: str = Field(description="Draft customer response")
    # the text the LLM suggests to send to the customer

    needs_escalation: bool = Field(
        description="Whether this case should be escalated"
    )
    # boolean indicating whether it must be passed to a human

    escalation_reason: str = Field(
        description="Why escalation is needed, if any"
    )
    # explanation of why escalation is recommended

    confidence: float = Field(description="Confidence from 0 to 1")
    # how confident the LLM is in this resolution
