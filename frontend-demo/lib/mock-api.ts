import type {
  AgentRunResult,
  Approval,
  AuditEvent,
  GovernanceStep,
  StepStatus,
} from "./types";
import { SCENARIOS } from "@/data/scenarios";
import { INITIAL_APPROVALS } from "@/data/approvals";
import { AUDIT_EVENTS } from "@/data/audit";

export type StepCallback = (
  index: number,
  status: StepStatus,
  detail: string
) => void;

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export async function runAgentScenario(
  scenarioId: string,
  onStep: StepCallback
): Promise<AgentRunResult> {
  const scenario = SCENARIOS.find((s) => s.id === scenarioId);
  if (!scenario) throw new Error(`Unknown scenario: ${scenarioId}`);

  const steps: GovernanceStep[] = scenario.steps.map((s) => ({
    id: s.id,
    label: s.label,
    description: s.description,
    status: "idle",
  }));

  const startTime = Date.now();

  for (let i = 0; i < scenario.steps.length; i++) {
    const stepDef = scenario.steps[i];

    if (stepDef.durationMs === 0) {
      steps[i].status = stepDef.finalStatus;
      steps[i].detail = stepDef.detail;
      onStep(i, stepDef.finalStatus, stepDef.detail);
      continue;
    }

    onStep(i, "running", stepDef.detail);
    await delay(stepDef.durationMs);
    steps[i].status = stepDef.finalStatus;
    steps[i].detail = stepDef.detail;
    steps[i].durationMs = stepDef.durationMs;
    onStep(i, stepDef.finalStatus, stepDef.detail);
  }

  const executionTimeMs = Date.now() - startTime;

  const statusMap: Record<string, AgentRunResult["status"]> = {
    ALLOWED: "COMPLETED",
    DENIED: "DENIED",
    BLOCKED: "BLOCKED",
    PENDING_APPROVAL: "INTERRUPTED_PENDING_APPROVAL",
  };

  return {
    threadId: `thr_${Math.random().toString(36).slice(2, 8)}`,
    traceId: `trc_${Math.random().toString(36).slice(2, 10)}`,
    status: statusMap[scenario.expectedDecision] ?? "COMPLETED",
    output: scenario.output,
    approvalId:
      scenario.expectedDecision === "PENDING_APPROVAL"
        ? "appr_c3d7f901"
        : undefined,
    governance: {
      identityVerified: true,
      policyDecision: scenario.expectedDecision,
      riskLevel: scenario.riskLevel,
      executionTimeMs,
      agentId: scenario.agentId,
      toolName: scenario.toolName,
      stepsCompleted: steps.filter((s) => s.status !== "idle").length,
    },
    steps,
  };
}

let _approvals: Approval[] = [...INITIAL_APPROVALS];

export function getApprovals(): Approval[] {
  return [..._approvals];
}

export async function resolveApproval(
  id: string,
  decision: "APPROVED" | "REJECTED",
  reason: string
): Promise<void> {
  await delay(300);
  _approvals = _approvals.map((a) =>
    a.id === id
      ? {
          ...a,
          status: decision,
          resolvedAt: new Date().toISOString(),
          resolvedBy: "usr_001",
          resolutionReason: reason,
        }
      : a
  );
}

let _auditEvents: AuditEvent[] = [...AUDIT_EVENTS];

export function getAuditEvents(): AuditEvent[] {
  return [..._auditEvents];
}

export function addAuditEvent(event: AuditEvent): void {
  _auditEvents = [event, ..._auditEvents];
}
