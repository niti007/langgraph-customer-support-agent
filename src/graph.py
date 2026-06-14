"""
Graph assembly — builds and compiles the LangGraph customer support workflow.
"""

import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.state import SupportState
from src.nodes import (
    classify_ticket,
    approval_gate,
    route_after_approval,
    retrieve_knowledge,
    draft_resolution,
    final_review_gate,
    route_resolution_or_escalation,
    resolve_case,
    escalate_case,
)


def build_graph(db_path: str = "support_agent_checkpoints.db"):
    """
    Construct the customer support agent graph with SQLite persistence.

    Args:
        db_path: Path to the SQLite database file for checkpoints.

    Returns:
        A compiled LangGraph ``CompiledGraph``.
    """
    builder = StateGraph(SupportState)

    # ── Nodes ──
    builder.add_node("classify_ticket", classify_ticket)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("draft_resolution", draft_resolution)
    builder.add_node("final_review_gate", final_review_gate)
    builder.add_node("resolve_case", resolve_case)
    builder.add_node("escalate_case", escalate_case)

    # ── Edges ──
    builder.add_edge(START, "classify_ticket")
    builder.add_edge("classify_ticket", "approval_gate")

    builder.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "retrieve_knowledge": "retrieve_knowledge",
            "escalate_case": "escalate_case",
        },
    )

    builder.add_edge("retrieve_knowledge", "draft_resolution")
    builder.add_edge("draft_resolution", "final_review_gate")

    builder.add_conditional_edges(
        "final_review_gate",
        route_resolution_or_escalation,
        {
            "resolve_case": "resolve_case",
            "escalate_case": "escalate_case",
        },
    )

    builder.add_edge("resolve_case", END)
    builder.add_edge("escalate_case", END)

    # ── Compile with persistence ──
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    graph = builder.compile(checkpointer=checkpointer)

    return graph
