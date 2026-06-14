"""
Interactive CLI for the LangGraph Customer Support Agent.

Usage:
    python main.py
"""

import json
import uuid

from langgraph.types import Command

from src.graph import build_graph


# ── Pretty-print helpers ──

def _print_section(title: str, content: str) -> None:
    """Print a labeled section to the terminal."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")
    print(content)


def _format_interrupt(interrupt_value: dict) -> str:
    """Format an interrupt payload for human review."""
    lines = []
    for key, value in interrupt_value.items():
        if key == "expected_reply_format":
            continue
        if isinstance(value, dict):
            lines.append(f"  {key}:")
            for k, v in value.items():
                lines.append(f"    {k}: {v}")
        else:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def _get_human_decision(interrupt_value: dict) -> dict:
    """Prompt the human reviewer and return their decision as a dict."""
    expected = interrupt_value.get("expected_reply_format", {})
    print("\n  Expected reply format:")
    for k, v in expected.items():
        print(f"    {k}: {v}")

    print()
    decision_input = input("  Your decision (JSON or plain text): ").strip()

    # Try parsing as JSON first
    try:
        return json.loads(decision_input)
    except json.JSONDecodeError:
        return {"decision": decision_input}


# ── Main loop ──

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║    LangGraph Customer Support Agent — Interactive CLI   ║")
    print("╚══════════════════════════════════════════════════════════╝")

    graph = build_graph()

    # Collect ticket input
    print()
    customer_id = input("  Customer ID (e.g. CUST_1001): ").strip() or "CUST_0000"
    customer_message = input("  Customer message: ").strip()

    if not customer_message:
        print("  ⚠  No message provided. Exiting.")
        return

    thread_id = f"{customer_id}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    ticket_input = {
        "customer_id": customer_id,
        "customer_message": customer_message,
    }

    _print_section("PROCESSING TICKET", f"  Thread: {thread_id}")

    # Run / resume loop
    result = graph.invoke(ticket_input, config=config)

    while True:
        interrupts = result.get("__interrupt__")
        if not interrupts:
            break

        # Handle human-in-the-loop interrupt
        interrupt_obj = interrupts[0]
        interrupt_value = interrupt_obj.value if hasattr(interrupt_obj, "value") else interrupt_obj

        _print_section("🔔 HUMAN REVIEW REQUIRED", _format_interrupt(interrupt_value))

        human_reply = _get_human_decision(interrupt_value)
        resume_cmd = Command(resume=human_reply)
        result = graph.invoke(resume_cmd, config=config)

    # Print final result
    _print_section(
        "✅ FINAL RESULT",
        f"  Status: {result.get('status', 'unknown')}\n"
        f"  Response:\n  {result.get('final_response', '(no response)')}"
    )


if __name__ == "__main__":
    main()
