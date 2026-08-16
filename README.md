# AegisGov

**Zero-Trust Execution Gateway & Secure Runtime Governance for Agentic AI**

> Agents propose actions. AegisGov owns execution authority.

AegisGov is a production-grade governance layer that sits between LLM agents and
any system-of-record they want to affect. Every tool call passes through
identity verification, OPA policy evaluation, risk classification, and (where
necessary) human approval before execution. Nothing reaches the database that
hasn't cleared every gate.

---

## Architecture overview

```
UNTRUSTED                          TRUSTED                        AUTHORIZED
──────────────────    ═══════════════════════════════    ─────────────────────
User → LLM/Agent  →  Keycloak JWT                    →  Secure Tool → PostgreSQL
  Proposed Action     + Agent workload JWT
                      + OPA policy (fail-closed)
                      + Pydantic v2 validation
                      + Risk classification
                      + HITL (CRITICAL / high-value)
                      + Audit (immutable)
```

Eight invariants enforced at all times (see `CLAUDE.md §8`):

1. No direct Agent → Tool execution — all traffic through the gateway
2. No Frontend → Authorization — server-side only
3. No LLM → Final policy decision — OPA is the sole decision point
4. OPA unavailable → DENY (fail-closed, never fail-open)
5. CRITICAL risk → always HITL, never auto-execute
6. Invalid params → no handler invocation
7. Unregistered tool → DENY
8. Rejected approval → no DB mutation

---

## Phase status

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Engineering contract (`CLAUDE.md`) | ✅ Complete |
| 1 | Foundation & Infrastructure | ✅ Complete |
| 2 | Identity + LangGraph agent runtime | ✅ Complete |
| 3 | Secure Tool Gateway + OPA rules | Pending |
| 4 | Audit + observability | Pending |
| 5 | Production UI | Pending |

---

## Local development

### Prerequisites

- Docker Desktop
- Python 3.12
- Node.js 20

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set AGENT_JWT_SECRET
```

### 2. Start all services

```bash
docker compose up -d
```

Services and ports:

| Service | URL |
|---------|-----|
| FastAPI backend | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| Next.js frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| OPA | http://localhost:8181 |
| Keycloak | http://localhost:8080 |

### 3. Run backend tests (without Docker)

```bash
cd backend
pip install -r requirements.txt
pytest
```

### 4. Run frontend in dev mode (without Docker)

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

---

## Repository structure

```
aegisgov/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── agents/       # Specialist agents (Phase 2)
│   │   ├── core/         # Config, identity, security
│   │   ├── db/           # SQLAlchemy models + session
│   │   ├── governance/   # Middleware, risk, policy (Phase 3)
│   │   ├── graph/        # LangGraph state + workflow (Phase 2)
│   │   ├── observability/# Langfuse tracer (Phase 4)
│   │   └── tools/        # Registry, schemas, handlers (Phase 3)
│   ├── tests/
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js 14 App Router pages
│   ├── components/       # Shared UI components (Phase 5)
│   ├── lib/              # Typed API client
│   ├── Dockerfile
│   └── package.json
├── keycloak/
│   └── realm-export.json # Dev realm: aegisgov
├── policy/
│   └── aegis_policy.rego # OPA policy (Phase 3)
├── schema/
│   └── init.sql          # PostgreSQL schema + seed data
├── tests/
│   └── e2e/              # End-to-end tests (Phase 5)
├── .env.example
├── CLAUDE.md             # Permanent engineering contract
└── docker-compose.yml
```

---

## Keycloak dev users

| User | Password | Role |
|------|----------|------|
| analyst_user | Password1! | analyst |
| billing_user | Password1! | billing |
| admin_user | Password1! | admin |

Realm: `aegisgov` · Client ID (frontend): `aegisgov-frontend`

---

## Interview positioning

AegisGov demonstrates:

- **Zero-trust security architecture**: fail-closed OPA, dual-identity model, no agent has DB credentials
- **Production async Python**: FastAPI + SQLAlchemy 2.0 async + asyncpg
- **Policy-as-code**: OPA/Rego as the sole authorization decision point
- **HITL in agentic systems**: LangGraph pause/resume with persistent approval state
- **Observability from day 1**: every governance decision written to immutable audit log
