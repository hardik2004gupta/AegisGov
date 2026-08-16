// Shared frontend types matching Phase 4 backend API contracts.

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";
export type AuditDecision = "ALLOWED" | "DENIED" | "BLOCKED" | "PENDING" | "APPROVED" | "REJECTED";
export type AgentRunStatus =
  | "COMPLETED"
  | "INTERRUPTED_PENDING_APPROVAL"
  | "DENIED"
  | "BLOCKED"
  | "FAILED"
  | "PROPOSAL_READY";

// ── Agent run ─────────────────────────────────────────────────────────────────

export interface GovernanceInfo {
  identity_verified: boolean;
  policy_decision: string;
  risk_level?: RiskLevel;
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

// ── Approvals ─────────────────────────────────────────────────────────────────

export interface ApprovalItem {
  approval_id: string;
  thread_id: string;
  trace_id?: string;
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

// ── Audit ─────────────────────────────────────────────────────────────────────

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

export interface AuditListResponse {
  items: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface TraceTimeline {
  trace_id: string;
  events: AuditEvent[];
  summary: {
    total_events: number;
    final_decision: string;
    user_ids: string[];
    agent_ids: string[];
    started_at?: string;
    completed_at?: string;
    decisions: Record<string, number>;
  };
}

// ── Runtime ───────────────────────────────────────────────────────────────────

export interface RuntimeStatus {
  summary: {
    total_decisions: number;
    allowed: number;
    denied: number;
    blocked: number;
    pending_approvals: number;
  };
  approvals: {
    pending: number;
    approved: number;
    rejected: number;
  };
  limits: {
    max_tool_calls: number;
    max_execution_time_seconds: number;
    max_agent_handoffs: number;
    max_identical_tool_calls: number;
  };
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface DependencyStatus {
  status: "healthy" | "unavailable" | "unconfigured" | string;
  latency_ms?: number;
  error?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | string;
  service: string;
  version: string;
  dependencies: {
    postgres: DependencyStatus;
    opa: DependencyStatus;
    keycloak: DependencyStatus;
    langfuse: DependencyStatus;
  };
}
