export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type Decision =
  | "ALLOWED"
  | "DENIED"
  | "BLOCKED"
  | "PENDING_APPROVAL"
  | "REJECTED"
  | "APPROVED";
export type StepStatus =
  | "idle"
  | "running"
  | "passed"
  | "failed"
  | "blocked"
  | "skipped"
  | "pending";
export type AgentId =
  | "supervisor"
  | "order-agent"
  | "billing-agent"
  | "admin-agent";
export type ToolName =
  | "get_order"
  | "get_customer"
  | "get_payment"
  | "issue_refund"
  | "delete_customer";
export type UserRole = "analyst" | "billing" | "admin";

export interface GovernanceStep {
  id: string;
  label: string;
  description: string;
  status: StepStatus;
  detail?: string;
  durationMs?: number;
}

export interface ScenarioStepDef {
  id: string;
  label: string;
  description: string;
  durationMs: number;
  finalStatus: StepStatus;
  detail: string;
}

export interface Scenario {
  id: string;
  title: string;
  description: string;
  userRole: UserRole;
  agentId: AgentId;
  toolName: ToolName;
  toolArgs: Record<string, unknown>;
  riskLevel: RiskLevel;
  expectedDecision: Decision;
  steps: ScenarioStepDef[];
  output: string;
}

export interface User {
  id: string;
  name: string;
  role: UserRole;
  sub: string;
}

export interface Tool {
  name: ToolName;
  description: string;
  risk: RiskLevel;
  requiresApproval: boolean | "conditional";
  approvalCondition?: string;
  dbRole: string;
  agents: AgentId[];
  schema: Record<string, string>;
}

export interface Agent {
  id: AgentId;
  name: string;
  spiffeId: string;
  tools: ToolName[];
  allowedRoles: UserRole[];
  description: string;
}

export interface Approval {
  id: string;
  traceId: string;
  threadId: string;
  toolName: ToolName;
  toolArgs: Record<string, unknown>;
  riskLevel: RiskLevel;
  agentId: AgentId;
  userId: string;
  userName: string;
  userRole: UserRole;
  status: "PENDING" | "APPROVED" | "REJECTED";
  reason: string;
  createdAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
  resolutionReason?: string;
}

export interface AuditEvent {
  id: string;
  traceId: string;
  userId: string;
  userName: string;
  agentId: AgentId | "system";
  actionType: string;
  decision: Decision | "PENDING" | "INTERRUPTED" | "IDENTITY_VERIFIED" | "INPUT_BLOCKED" | "AGENT_HANDOFF_ALLOWED" | "AGENT_HANDOFF_DENIED";
  reason: string;
  riskLevel?: RiskLevel;
  toolName?: ToolName;
  payload?: Record<string, unknown>;
  createdAt: string;
}

export interface RuntimeMetrics {
  totalProposals: number;
  allowed: number;
  denied: number;
  blocked: number;
  pendingApprovals: number;
  avgExecutionMs: number;
  toolCallBudget: number;
  toolCallsUsed: number;
  handoffBudget: number;
  handoffsUsed: number;
  maxIdenticalCalls: number;
  uptimeSeconds: number;
  lastUpdated: string;
}

export interface AgentRunResult {
  threadId: string;
  traceId: string;
  status: "COMPLETED" | "DENIED" | "BLOCKED" | "INTERRUPTED_PENDING_APPROVAL";
  output: string;
  approvalId?: string;
  governance: {
    identityVerified: boolean;
    policyDecision: Decision | "PENDING_APPROVAL";
    riskLevel: RiskLevel;
    executionTimeMs: number;
    agentId: AgentId;
    toolName?: ToolName;
    stepsCompleted: number;
  };
  steps: GovernanceStep[];
}
