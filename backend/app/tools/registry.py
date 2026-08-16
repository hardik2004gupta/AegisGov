# Phase 3: Tool Registry
#
# The registry is the authoritative list of executable tools.
# Unregistered tools fail closed — no execution attempt is made.
#
# CLAUDE.md §9 — every tool entry contains:
#   name                    str
#   schema                  Pydantic BaseModel class
#   risk_level              "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
#   requires_human_approval bool (static flag; dynamic check in risk.py)
#   target_db_role          str  (used by handlers.py for least-priv access)
#   handler                 Callable
#
# Canonical registry (CLAUDE.md §9):
#   get_order       LOW      order_reader
#   get_customer    LOW      order_reader
#   get_payment     MEDIUM   billing_reader
#   issue_refund    HIGH     billing_writer   (HITL if amount > $500)
#   delete_customer CRITICAL admin_writer     (HITL always)

from __future__ import annotations

# TODO Phase 3: populate TOOL_REGISTRY dict with all 5 entries
