"""
Langfuse Observability Tracer — CLAUDE.md §18, Phase 4

OPTIONAL: If Langfuse is not configured or the SDK is unavailable, all calls
are no-ops. Langfuse failure NEVER changes security decisions.

PostgreSQL audit_events is the governance system of record.
Langfuse provides LLM/agent observability spans only.

Each execution trace (CLAUDE.md §18):
    Trace ID
      ├── Identity
      ├── Agent Decision
      ├── Tool Proposal
      ├── OPA Decision
      ├── Risk Classification
      ├── Execution
      └── Final Decision
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try importing the Langfuse SDK — remains None if not installed.
_Langfuse: type | None = None
try:
    from langfuse import Langfuse as _Langfuse  # type: ignore[no-redef,import-not-found]
except ImportError:
    pass

_client: Any = None


def is_enabled() -> bool:
    """Return True only when Langfuse is fully configured AND the SDK is installed."""
    return (
        settings.langfuse_enabled
        and bool(settings.langfuse_public_key)
        and _Langfuse is not None
    )


def _get_client() -> Any:
    """Return (or lazily create) the shared Langfuse client; None if unavailable."""
    global _client
    if _client is not None:
        return _client
    if not is_enabled():
        return None
    try:
        _client = _Langfuse(  # type: ignore[misc]
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse client initialized host=%s", settings.langfuse_host)
    except Exception as exc:
        logger.warning("Langfuse client init failed (non-fatal): %s", exc)
        _client = None
    return _client


# ─── Trace context ─────────────────────────────────────────────────────────────


class TraceContext:
    """Thin wrapper around a Langfuse trace. All methods no-op if unavailable."""

    def __init__(self, trace: Any = None) -> None:
        self._trace = trace

    def add_span(
        self,
        name: str,
        *,
        input: Any = None,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._trace is None:
            return
        try:
            self._trace.span(name=name, input=input, output=output, metadata=metadata or {})
        except Exception as exc:
            logger.debug("Langfuse span error (non-fatal): %s", exc)

    def add_generation(
        self,
        name: str,
        *,
        model: str = "",
        input: Any = None,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._trace is None:
            return
        try:
            self._trace.generation(
                name=name, model=model, input=input, output=output, metadata=metadata or {}
            )
        except Exception as exc:
            logger.debug("Langfuse generation error (non-fatal): %s", exc)

    def record_governance(
        self,
        event_type: str,
        decision: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a governance checkpoint as a span."""
        self.add_span(
            name=f"governance.{event_type.lower()}",
            metadata={"decision": decision, **(metadata or {})},
        )


# ─── Public API ────────────────────────────────────────────────────────────────


def create_trace(
    trace_id: str,
    name: str,
    *,
    user_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> TraceContext:
    """Create a Langfuse trace for a single agent execution.

    Returns a no-op TraceContext if Langfuse is unavailable.
    """
    client = _get_client()
    if client is None:
        return TraceContext()
    try:
        trace = client.trace(
            id=trace_id,
            name=name,
            user_id=user_id or None,
            metadata=metadata or {},
        )
        return TraceContext(trace)
    except Exception as exc:
        logger.debug("Langfuse create_trace error (non-fatal): %s", exc)
        return TraceContext()


def flush() -> None:
    """Flush pending Langfuse events. No-op if unavailable."""
    client = _get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:
        logger.debug("Langfuse flush error (non-fatal): %s", exc)
