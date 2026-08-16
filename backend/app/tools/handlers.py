# Phase 3: Tool Handlers — Secure DB Operations
#
# These are the ONLY functions that may execute database mutations.
# They are called exclusively by the Secure Tool Gateway after the
# full pipeline has passed (Registry → Pydantic → OPA → Risk → HITL).
#
# ARCHITECTURAL INVARIANT (CLAUDE.md §8):
#   Agents must never invoke these functions directly.
#   Only the gateway may call a handler — after all checks pass.
#
# Each handler connects using the minimum required PostgreSQL role
# determined by the tool registry's target_db_role field.
# Agents never receive database credentials (CLAUDE.md §17).

from __future__ import annotations

# TODO Phase 3: implement handler functions for all 5 tools
# get_order_handler, get_customer_handler, get_payment_handler,
# issue_refund_handler, delete_customer_handler
