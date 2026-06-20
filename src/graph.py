"""
Graph assembly — builds and compiles the LangGraph customer support workflow.
"""
# (Docstring explaining this module builds the workflow graph.)

import sqlite3
# import SQLite to store persistent checkpoints

from langgraph.graph import StateGraph, START, END
# import the StateGraph builder and special START/END node markers

from langgraph.checkpoint.sqlite import SqliteSaver
# import a helper to save graph checkpoints to SQLite

from src.state import SupportState
# import the typed state shape used by the graph

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
# import all node functions and routing helpers used in the graph

def build_graph(db_path: str = "support_agent_checkpoints.db"):
    """
    Construct the customer support agent graph with SQLite persistence.

    Args:
        db_path: Path to the SQLite database file for checkpoints.

    Returns:
        A compiled LangGraph ``CompiledGraph``.
    """
    # function docstring describing parameters and return

    builder = StateGraph(SupportState)
    # create a graph builder that uses SupportState as the state type

    # ── Nodes ──
    builder.add_node("classify_ticket", classify_ticket)
    # add the classify_ticket node to the graph

    builder.add_node("approval_gate", approval_gate)
    # add the human approval gate node to the graph

    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    # add the node that retrieves knowledge-base articles

    builder.add_node("draft_resolution", draft_resolution)
    # add the node that asks the LLM to draft a response

    builder.add_node("final_review_gate", final_review_gate)
    # add the second human review gate node

    builder.add_node("resolve_case", resolve_case)
    # add the node that marks a case as resolved

    builder.add_node("escalate_case", escalate_case)
    # add the node that escalates the case to a human specialist

    # ── Edges ──
    builder.add_edge(START, "classify_ticket")
    # connect the graph start to classification

    builder.add_edge("classify_ticket", "approval_gate")
    # after classification, go to approval gate

    builder.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "retrieve_knowledge": "retrieve_knowledge",
            "escalate_case": "escalate_case",
        },
    )
    # from approval gate, pick next node using route_after_approval function;
    # map names for clarity (retrieve_knowledge or escalate_case)

    builder.add_edge("retrieve_knowledge", "draft_resolution")
    # after retrieving knowledge, draft a resolution

    builder.add_edge("draft_resolution", "final_review_gate")
    # after drafting, send to final human review

    builder.add_conditional_edges(
        "final_review_gate",
        route_resolution_or_escalation,
        {
            "resolve_case": "resolve_case",
            "escalate_case": "escalate_case",
        },
    )
    # route after final review to either resolve or escalate based on function

    builder.add_edge("resolve_case", END)
    # resolving the case goes to the graph end

    builder.add_edge("escalate_case", END)
    # escalating the case also goes to the graph end

    # ── Compile with persistence ──
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # open a SQLite connection to store checkpoints (allow use from multiple threads)

    checkpointer = SqliteSaver(conn)
    # create a checkpointer that writes to the SQLite connection

    graph = builder.compile(checkpointer=checkpointer)
    # compile the graph and attach the checkpointer for persistence

    return graph
    # return the compiled graph object
