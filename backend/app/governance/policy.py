"""
Policy Decision Service

This is the single interface for all authorization policy decisions.

Phase 2: Deterministic in-process implementation using the canonical
    role → agent mapping from CLAUDE.md §13.

Phase 3: Replace allow_handoff() (and add allow_tool_execution()) with
    OPA REST calls. The graph nodes and specialist agents must not change —
    only this module changes to make OPA the decision point.

CLAUDE.md §24 Rule 4: OPA is the Policy Decision Point.
    Do not duplicate authorization logic in handlers or middleware.
    This module is the sole location for policy decisions.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ─── Role → Agent policy (CLAUDE.md §13) ─────────────────────────────────────

_ROLE_AGENT_POLICY: dict[str, list[str]] = {
    "analyst": ["order-agent"],
    "billing": ["order-agent", "billing-agent"],
    "admin": ["order-agent", "billing-agent", "admin-agent"],
}


class PolicyDecisionService:
    """Authorization policy decisions for the AegisGov governance pipeline.

    Phase 2: deterministic. Phase 3: backed by OPA REST API.
    Callers (graph nodes) are not aware of the underlying implementation.
    """

    def allow_handoff(self, user_roles: list[str], target_agent: str) -> bool:
        """Return True iff any of the user's roles authorizes handoff to target_agent.

        Phase 2 implementation: checks the canonical ROLE_AGENT_POLICY table.
        Phase 3: this method will call OPA and return the policy decision.

        Fail-closed: if roles is empty or target_agent is unknown, returns False.
        """
        if not user_roles or not target_agent:
            return False
        for role in user_roles:
            if target_agent in _ROLE_AGENT_POLICY.get(role, []):
                logger.debug(
                    "Handoff ALLOWED: role=%s target=%s",
                    role,
                    target_agent,
                )
                return True
        logger.info(
            "Handoff DENIED: roles=%s target=%s (Phase 2 policy)",
            user_roles,
            target_agent,
        )
        return False

    # Phase 3 will add:
    # async def allow_tool_execution(self, context: RequestContext, tool_name: str, ...) -> PolicyResult: ...


# Module-level singleton used by graph nodes.
# Phase 3 replaces this with an OPA-backed instance.
policy_service = PolicyDecisionService()
