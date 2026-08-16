# Phase 2: Security Utilities
#
# Shared security helpers used across the application:
#   - Agent workload JWT signing / verification
#   - Workload identity URI construction (aegis://agents/...)
#   - Request header utilities
#
# CLAUDE.md §5 — Agent Identity:
#   Each agent has a distinct workload identity URI.
#   The MVP represents this with signed internal JWTs.
#   The architecture is extensible toward SPIFFE/SVID.

from __future__ import annotations

# TODO Phase 2: implement workload JWT helpers
