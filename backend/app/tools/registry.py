"""
Tool Registry — CLAUDE.md §9

The authoritative list of executable tools. Unregistered tools fail closed —
no execution attempt is made (INVARIANT 7, CLAUDE.md §26).

Every entry contains (CLAUDE.md §9):
    name                    str
    schema                  Pydantic BaseModel class
    risk_level              "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    requires_human_approval bool  (static; runtime check in risk.py)
    target_db_role          str   (gateway selects this role for execution)
    handler                 Callable

Do not dynamically import arbitrary functions based on an LLM-generated
tool name. Only these five tools are executable (CLAUDE.md §3).
"""

from __future__ import annotations

from typing import Any, Callable

from app.tools.schemas import (
    DeleteCustomerSchema,
    GetCustomerSchema,
    GetOrderSchema,
    GetPaymentSchema,
    IssueRefundSchema,
)

# Handlers imported here so the registry owns the only reference.
# Agents must NOT import handlers.py directly.
from app.tools.handlers import (
    delete_customer_handler,
    get_customer_handler,
    get_order_handler,
    get_payment_handler,
    issue_refund_handler,
)


class ToolRegistryEntry(dict):
    """Typed alias for clarity — dict keys are documented in CLAUDE.md §9."""


TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "get_order": {
        "name": "get_order",
        "schema": GetOrderSchema,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "target_db_role": "order_reader",
        "handler": get_order_handler,
    },
    "get_customer": {
        "name": "get_customer",
        "schema": GetCustomerSchema,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "target_db_role": "order_reader",
        "handler": get_customer_handler,
    },
    "get_payment": {
        "name": "get_payment",
        "schema": GetPaymentSchema,
        "risk_level": "MEDIUM",
        "requires_human_approval": False,
        "target_db_role": "billing_reader",
        "handler": get_payment_handler,
    },
    "issue_refund": {
        "name": "issue_refund",
        "schema": IssueRefundSchema,
        "risk_level": "HIGH",
        "requires_human_approval": False,  # dynamic: True when amount > $500
        "target_db_role": "billing_writer",
        "handler": issue_refund_handler,
    },
    "delete_customer": {
        "name": "delete_customer",
        "schema": DeleteCustomerSchema,
        "risk_level": "CRITICAL",
        "requires_human_approval": True,  # always requires HITL
        "target_db_role": "admin_writer",
        "handler": delete_customer_handler,
    },
}


def get_tool(name: str) -> dict[str, Any] | None:
    """Look up a tool by name. Returns None for unregistered tools (fail closed)."""
    return TOOL_REGISTRY.get(name)


def is_registered(name: str) -> bool:
    """Return True iff the tool name is in the registry."""
    return name in TOOL_REGISTRY
