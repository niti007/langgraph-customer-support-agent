"""
Pydantic models for structured LLM outputs.
"""

from typing import Literal
from pydantic import BaseModel, Field


class TicketClassification(BaseModel):
    """Structured classification of a customer support ticket."""

    category: Literal["billing", "technical", "order", "account", "general"] = Field(
        description="Main category of the support ticket"
    )
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
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Urgency of the ticket"
    )
    sentiment: Literal["positive", "neutral", "negative", "frustrated"] = Field(
        description="Customer sentiment"
    )
    confidence: float = Field(description="Confidence from 0 to 1")
    rationale: str = Field(description="Short explanation")


class ResolutionDecision(BaseModel):
    """Structured resolution drafted by the LLM."""

    draft_response: str = Field(description="Draft customer response")
    needs_escalation: bool = Field(
        description="Whether this case should be escalated"
    )
    escalation_reason: str = Field(
        description="Why escalation is needed, if any"
    )
    confidence: float = Field(description="Confidence from 0 to 1")
