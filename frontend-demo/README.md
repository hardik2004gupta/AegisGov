# AegisGov — Frontend Demo

A fully standalone, interactive product demo for [AegisGov](../README.md).

**Zero dependencies on the backend** — runs entirely from local TypeScript mock data. No PostgreSQL, Keycloak, OPA, or Langfuse required.

## Quick start

```bash
cd frontend-demo
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Pages

| Page | Path | Description |
|------|------|-------------|
| Overview | `/overview` | Architecture, invariants, governed tools |
| Agent Console | `/agent` | Run 5 interactive demo scenarios |
| Approval Queue | `/approvals` | Approve / reject pending HITL actions |
| Audit Explorer | `/audit` | Searchable, trace-linked audit log |
| Runtime Dashboard | `/runtime` | Budget gauges, metrics, threat coverage |
| Tool Registry | `/tools` | All 5 governed tools with schemas |
| Agent Registry | `/agents` | Agent topology and authorization matrix |

## Demo scenarios (Agent Console)

1. **Read Order** — analyst + get_order → LOW risk → ALLOWED
2. **Refund $120** — billing + issue_refund($120) → HIGH, below $500 → ALLOWED
3. **Delete Customer** — admin + delete_customer → CRITICAL → PENDING_APPROVAL
4. **Privilege Escalation** — analyst attempts admin-agent → DENIED at handoff
5. **Prompt Injection** — malicious input → BLOCKED at guardrails

## Deploy to Vercel

```bash
cd frontend-demo
npx vercel --prod
```

No environment variables required.
