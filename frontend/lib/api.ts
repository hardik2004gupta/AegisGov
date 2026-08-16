// Typed API client for the AegisGov backend.
// Phase 5 will expand each namespace with full CRUD operations.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export const health = {
  get: () => request<HealthResponse>("/health"),
};

// ── Governance approvals (Phase 3+) ──────────────────────────────────────────

export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ApprovalRequest {
  id: string;
  thread_id: string;
  user_id: string;
  agent_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  risk_level: RiskLevel;
  reason: string;
  status: ApprovalStatus;
  created_at: string;
}

export const approvals = {
  list: () => request<ApprovalRequest[]>("/api/v1/governance/approvals"),
  resolve: (id: string, decision: "approved" | "rejected") =>
    request<void>(`/api/v1/governance/approvals/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),
};

// ── Audit events (Phase 4+) ───────────────────────────────────────────────────

export type AuditDecision = "ALLOW" | "DENY" | "HITL";

export interface AuditEvent {
  id: string;
  trace_id: string;
  user_id: string;
  agent_id: string;
  tool_name: string;
  decision: AuditDecision;
  risk_level: RiskLevel;
  reason: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export const audit = {
  list: () => request<AuditEvent[]>("/api/v1/audit"),
  get: (traceId: string) => request<AuditEvent[]>(`/api/v1/audit/${traceId}`),
};
