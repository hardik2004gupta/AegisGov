# Phase 4: Langfuse Observability Tracer
#
# Wraps Langfuse trace/span creation for each AegisGov execution.
# Langfuse is the observability layer — not the system of record.
# Governance decisions are ALWAYS written to PostgreSQL audit_events.
# Langfuse is optional; if credentials are missing the app still runs.
#
# Each execution trace (CLAUDE.md §18):
#   Trace ID
#     ├── User
#     ├── Agent
#     ├── User Prompt
#     ├── Agent Decision
#     ├── Tool Proposal
#     ├── OPA Decision
#     ├── Risk Classification
#     ├── Execution
#     ├── Result
#     └── Final Decision

from __future__ import annotations

from app.core.config import settings


def is_enabled() -> bool:
    return settings.langfuse_enabled and bool(settings.langfuse_public_key)


# TODO Phase 4: implement Langfuse trace helpers
# create_trace(), add_span(), record_governance_event(), flush()
