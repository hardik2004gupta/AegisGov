"""
OPA Policy Decision Service — CLAUDE.md §11, §24 Rule 4

This is the single interface for all authorization policy decisions.
OPA is the authoritative Policy Decision Point. Authorization logic must
not be duplicated in handlers, middleware, or route guards.

Phase 3: replaced deterministic in-process logic with OPA REST API calls.

FAIL-CLOSED contract (CLAUDE.md §11, §16):
    OPA unavailable → DENY
    OPA timeout     → DENY
    OPA error       → DENY
    Malformed response → DENY
    Unknown policy result → DENY
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_OPA_TIMEOUT = 5.0  # seconds — fail closed on timeout


@dataclass
class PolicyResult:
    allow: bool
    require_human_approval: bool
    reason: str


_DENY_RESULT = PolicyResult(allow=False, require_human_approval=False, reason="denied")
_OPA_DENY = PolicyResult(allow=False, require_human_approval=False, reason="OPA unavailable or error — fail closed")


class OPAPolicyService:
    """OPA-backed policy decision service (CLAUDE.md §11).

    Callers (graph nodes, gateway) should use the module-level `policy_service`
    singleton. They should not instantiate this class directly.
    """

    async def _query_opa(self, input_data: dict) -> PolicyResult:
        """Send a policy query to OPA and return a structured decision.

        Fail-closed: any failure returns DENY.
        """
        url = settings.opa_decision_url
        payload = {"input": input_data}
        try:
            async with httpx.AsyncClient(timeout=_OPA_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()

            body = resp.json()
            result = body.get("result")

            if not isinstance(result, dict):
                logger.error(
                    "OPA returned non-dict result type=%s — DENY",
                    type(result).__name__,
                )
                return _OPA_DENY

            allow = result.get("allow")
            if not isinstance(allow, bool):
                logger.error(
                    "OPA 'allow' field missing or not bool value=%r — DENY",
                    allow,
                )
                return _OPA_DENY

            require_human_approval = bool(result.get("require_human_approval", False))
            reason = str(result.get("reason", "allowed" if allow else "denied"))

            return PolicyResult(
                allow=allow,
                require_human_approval=require_human_approval,
                reason=reason,
            )

        except httpx.TimeoutException:
            logger.error("OPA request timed out url=%s — DENY", url)
            return _OPA_DENY
        except httpx.HTTPStatusError as exc:
            logger.error(
                "OPA HTTP error %s url=%s — DENY",
                exc.response.status_code,
                url,
            )
            return _OPA_DENY
        except httpx.RequestError as exc:
            logger.error("OPA connection error url=%s — DENY: %s", url, exc)
            return _OPA_DENY
        except Exception as exc:
            logger.exception("Unexpected OPA error — DENY: %s", exc)
            return _OPA_DENY

    async def allow_handoff(
        self,
        user_id: str,
        user_roles: list[str],
        agent_id: str,
        agent_spiffe_id: str,
        target_agent: str,
    ) -> PolicyResult:
        """Evaluate whether the user's roles authorize a handoff to target_agent.

        Fail-closed: if roles is empty, OPA will deny by default policy.
        """
        if not user_roles or not target_agent:
            logger.info(
                "Handoff DENIED before OPA: empty roles or no target agent=%r",
                target_agent,
            )
            return _DENY_RESULT

        input_data = {
            "user": {"id": user_id, "roles": user_roles},
            "agent": {"id": agent_id, "spiffe_id": agent_spiffe_id},
            "action": {"type": "agent_handoff", "name": target_agent},
            "resource": {"type": "agent", "id": target_agent},
        }
        result = await self._query_opa(input_data)
        logger.info(
            "Handoff OPA decision: roles=%s target=%s allow=%s",
            user_roles, target_agent, result.allow,
        )
        return result

    async def allow_tool_execution(
        self,
        user_id: str,
        user_roles: list[str],
        agent_id: str,
        agent_spiffe_id: str,
        tool_name: str,
        resource_id: str = "",
        arguments: dict | None = None,
    ) -> PolicyResult:
        """Evaluate whether the actor is authorized to execute a tool.

        Includes the validated amount for issue_refund so OPA can
        determine require_human_approval for the $500 threshold.
        """
        if not user_roles or not tool_name:
            return _DENY_RESULT

        action: dict = {"type": "tool_execution", "name": tool_name}

        # Pass amount for OPA's refund threshold check (CLAUDE.md §19)
        if tool_name == "issue_refund" and arguments:
            action["amount"] = float(arguments.get("amount", 0))

        input_data = {
            "user": {"id": user_id, "roles": user_roles},
            "agent": {"id": agent_id, "spiffe_id": agent_spiffe_id},
            "action": action,
            "resource": {"type": "tool", "id": resource_id or tool_name},
        }
        result = await self._query_opa(input_data)
        logger.info(
            "Tool OPA decision: roles=%s agent=%s tool=%s allow=%s hitl=%s",
            user_roles, agent_id, tool_name, result.allow, result.require_human_approval,
        )
        return result


# Module-level singleton used by graph nodes and the gateway.
policy_service = OPAPolicyService()
