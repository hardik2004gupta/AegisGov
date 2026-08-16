// Typed API client for the AegisGov backend — Phase 5.
// All methods are strongly typed; no `any`.

import type {
  AgentRunResponse,
  ApprovalItem,
  AuditListResponse,
  HealthResponse,
  ResolveResponse,
  RuntimeStatus,
  TraceTimeline,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body?.detail ?? "";
    } catch {
      /* ignore parse error */
    }
    throw new ApiError(res.status, path, detail);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly path: string,
    public readonly detail: string,
  ) {
    super(detail || `API ${status}: ${path}`);
    this.name = "ApiError";
  }
}

// ── Agent ─────────────────────────────────────────────────────────────────────

export const agent = {
  run: (message: string, threadId: string, bearerToken: string): Promise<AgentRunResponse> =>
    request<AgentRunResponse>("/api/v1/agent/run", {
      method: "POST",
      headers: { Authorization: `Bearer ${bearerToken}` },
      body: JSON.stringify({ thread_id: threadId, message }),
    }),
};

// ── Approvals ─────────────────────────────────────────────────────────────────

export interface ApprovalsListParams {
  status?: string;
  risk_level?: string;
  agent_id?: string;
  user_id?: string;
  limit?: number;
  pending_only?: boolean;
}

export const approvals = {
  list: (params: ApprovalsListParams = {}): Promise<ApprovalItem[]> => {
    const q = new URLSearchParams();
    if (params.status)     q.set("status", params.status);
    if (params.risk_level) q.set("risk_level", params.risk_level);
    if (params.agent_id)   q.set("agent_id", params.agent_id);
    if (params.user_id)    q.set("user_id", params.user_id);
    if (params.limit)      q.set("limit", String(params.limit));
    if (params.pending_only !== undefined) q.set("pending_only", String(params.pending_only));
    return request<ApprovalItem[]>(`/api/v1/governance/approvals?${q}`);
  },

  get: (id: string): Promise<ApprovalItem> =>
    request<ApprovalItem>(`/api/v1/governance/approvals/${id}`),

  resolve: (
    id: string,
    decision: "APPROVED" | "REJECTED",
    resolution_reason: string,
    bearerToken: string,
  ): Promise<ResolveResponse> =>
    request<ResolveResponse>(`/api/v1/governance/approvals/${id}/resolve`, {
      method: "POST",
      headers: { Authorization: `Bearer ${bearerToken}` },
      body: JSON.stringify({ decision, resolution_reason }),
    }),
};

// ── Audit ─────────────────────────────────────────────────────────────────────

export interface AuditListParams {
  trace_id?: string;
  user_id?: string;
  agent_id?: string;
  decision?: string;
  action_type?: string;
  limit?: number;
  offset?: number;
}

export const audit = {
  list: (params: AuditListParams = {}): Promise<AuditListResponse> => {
    const q = new URLSearchParams();
    if (params.trace_id)    q.set("trace_id", params.trace_id);
    if (params.user_id)     q.set("user_id", params.user_id);
    if (params.agent_id)    q.set("agent_id", params.agent_id);
    if (params.decision)    q.set("decision", params.decision);
    if (params.action_type) q.set("action_type", params.action_type);
    if (params.limit)       q.set("limit", String(params.limit));
    if (params.offset)      q.set("offset", String(params.offset));
    return request<AuditListResponse>(`/api/v1/audit?${q}`);
  },

  trace: (traceId: string): Promise<TraceTimeline> =>
    request<TraceTimeline>(`/api/v1/audit/${traceId}`),
};

// ── Runtime ───────────────────────────────────────────────────────────────────

export const runtime = {
  status: (bearerToken?: string): Promise<RuntimeStatus> =>
    request<RuntimeStatus>("/api/v1/runtime/status", bearerToken
      ? { headers: { Authorization: `Bearer ${bearerToken}` } }
      : {}),
};

// ── Health ────────────────────────────────────────────────────────────────────

export const health = {
  get: (): Promise<HealthResponse> => request<HealthResponse>("/health"),
};

// Re-export legacy names used in existing page.tsx to avoid breaking it during transition
export const agentRun = {
  submit: agent.run,
};

export type { AgentRunResponse, ApprovalItem, AuditListResponse, HealthResponse, ResolveResponse, RuntimeStatus, TraceTimeline };
export type { AgentRunStatus, GovernanceInfo, AgentProposal, AgentInfo, AuditEvent, RiskLevel, ApprovalStatus, AuditDecision } from "./types";
