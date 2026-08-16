# Phase 3: Risk Classification
#
# Classifies tool proposals by risk level and determines whether
# human approval is required before execution.
#
# Risk levels (CLAUDE.md §14):
#   LOW      → get_order, get_customer       → auto-execute
#   MEDIUM   → get_payment                  → auto-execute (correct perms)
#   HIGH     → issue_refund                 → auto if ≤$500; HITL if >$500
#   CRITICAL → delete_customer              → ALWAYS pause for human approval
#
# This module classifies risk from the tool registry metadata and
# any dynamic context (e.g. refund amount). It does not make
# policy decisions — that is OPA's role.

from __future__ import annotations

# TODO Phase 3: implement risk classification logic
