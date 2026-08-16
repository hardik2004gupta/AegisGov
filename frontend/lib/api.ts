// Typed API client for the AegisGov backend.
// Phase 3: added approval/execution result types and governance fields.

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

// ── Agent run (Phase 3) ───────────────────────────────────────────────────────

export interface GovernanceInfo {
  identity_verified: boolean;
  policy_decision: string;
  risk_level?: string;
  execution_time_ms?: number;
  agent_id?: string;
  agent_spiffe_id?: string;
}

export interface AgentProposal {
  tool: string;
  arguments: Record<string, unknown>;
  reason?: string;
}

export interface AgentInfo {
  id: string;
  spiffe_id?: string;
  capabilities?: string[];
}

export type AgentRunStatus =
  | "PROPOSAL_READY"
  | "COMPLETED"
  | "INTERRUPTED_PENDING_APPROVAL"
  | "DENIED"
  | "BLOCKED"
  | "FAILED";

export interface AgentRunResponse {
  thread_id: string;
  status: AgentRunStatus;
  trace_id: string;
  output?: string;
  error?: string;
  approval_id?: string;
  execution_result?: Record<string, unknown>;
  agent?: AgentInfo;
  proposal?: AgentProposal;
  governance: GovernanceInfo;
}

export const agentRun = {
  submit: (
    message: string,
    threadId: string,
    bearerToken: string,
  ): Promise<AgentRunResponse> =>
    request<AgentRunResponse>("/api/v1/agent/run", {
      method: "POST",
      headers: { Authorization: `Bearer ${bearerToken}` },
      body: JSON.stringify({ thread_id: threadId, message }),
    }),
};

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export const health = {
  get: () => request<HealthResponse>("/health"),
};

// ── Governance approvals (Phase 3) ────────────────────────────────────────────

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface ApprovalItem {
  approval_id: string;
  thread_id: string;
  agent_id: string;
  user_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  risk_level: RiskLevel;
  status: ApprovalStatus;
  approved_by?: string;
  resolution_reason?: string;
  created_at: string;
  resolved_at?: string;
}

export interface ResolveResponse {
  approval_id: string;
  decision: string;
  tool_name: string;
  execution_result?: Record<string, unknown>;
  message: string;
}

export const approvals = {
  list: (pendingOnly = true): Promise<ApprovalItem[]> =>
    request<ApprovalItem[]>(`/api/v1/governance/approvals?pending_only=${pendingOnly}`),

  get: (id: string): Promise<ApprovalItem> =>
    request<ApprovalItem>(`/api/v1/governance/approvals/${id}`),

  resolve: (
    id: string,
    decision: "APPROVED" | "REJECTED",
    reason: string,
    bearerToken: string,
  ): Promise<ResolveResponse> =>
    request<ResolveResponse>(`/api/v1/governance/approvals/${id}/resolve`, {
      method: "POST",
      headers: { Authorization: `Bearer ${bearerToken}` },
      body: JSON.stringify({ decision, resolution_reason: reason }),
    }),
};

// ── Audit events (Phase 4+) ───────────────────────────────────────────────────

export type AuditDecision = "ALLOWED" | "DENIED" | "BLOCKED" | "PENDING" | "APPROVED" | "REJECTED";

export interface AuditEvent {
  id: string;
  trace_id: string;
  user_id: string;
  agent_id: string;
  action_type: string;
  decision: AuditDecision;
  reason?: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export const audit = {
  list: () => request<AuditEvent[]>("/api/v1/audit"),
  get: (traceId: string) => request<AuditEvent[]>(`/api/v1/audit/${traceId}`),
};
