# Phase 2: Human Identity — JWT Verification
#
# This module verifies Keycloak-issued JWTs and extracts the
# human identity used throughout the authorization pipeline.
#
# CLAUDE.md §5 — Critical rule:
#   Authorization MUST derive from verified JWT claims only.
#   Role information in the request body is UNTRUSTED and ignored.
#
# JWT claims of interest:
#   sub                  — user ID
#   preferred_username   — display name
#   realm_access.roles   — role list (analyst | billing | admin)
#
# Phase 2 implements:
#   - JWKS fetch from Keycloak
#   - RS256 token verification
#   - Role extraction
#   - FastAPI dependency: get_current_user

from __future__ import annotations

# TODO Phase 2: implement JWT verification and user extraction
