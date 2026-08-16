"use client";

export type StepState = "idle" | "active" | "success" | "warning" | "denied" | "blocked";

export interface PipelineStep {
  id: string;
  label: string;
  state: StepState;
  detail?: string;
}

const STATE_STYLES: Record<StepState, { icon: React.ReactNode; ring: string; dot: string; text: string }> = {
  idle:    { icon: <CircleIcon />,  ring: "border-[#e4e7ec]", dot: "bg-[#e4e7ec]", text: "text-[#94a3b8]" },
  active:  { icon: <SpinIcon />,   ring: "border-aegis-300", dot: "bg-aegis-400",  text: "text-aegis-600" },
  success: { icon: <CheckIcon />,  ring: "border-emerald-300", dot: "bg-emerald-500", text: "text-emerald-700" },
  warning: { icon: <WarnIcon />,   ring: "border-amber-300", dot: "bg-amber-400",  text: "text-amber-700" },
  denied:  { icon: <XIcon />,      ring: "border-red-300",   dot: "bg-red-500",    text: "text-red-700" },
  blocked: { icon: <BlockIcon />,  ring: "border-orange-300", dot: "bg-orange-500", text: "text-orange-700" },
};

interface GovernancePipelineProps {
  steps: PipelineStep[];
  compact?: boolean;
}

export function GovernancePipeline({ steps, compact = false }: GovernancePipelineProps) {
  return (
    <div className={compact ? "flex items-start gap-0" : "flex flex-col gap-0"}>
      {steps.map((step, i) => {
        const s = STATE_STYLES[step.state];
        const isLast = i === steps.length - 1;

        if (compact) {
          return (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`w-6 h-6 rounded-full border flex items-center justify-center flex-shrink-0 transition-all duration-200 ${s.ring} bg-white`}
                  title={step.label}
                >
                  {s.icon}
                </div>
              </div>
              {!isLast && (
                <div className="w-8 h-px bg-[#e4e7ec] flex-shrink-0 mx-0.5" />
              )}
            </div>
          );
        }

        return (
          <div key={step.id} className="flex gap-3">
            {/* Left column: dot + connector */}
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all duration-200 ${s.ring} bg-white`}
              >
                {s.icon}
              </div>
              {!isLast && (
                <div className="w-px flex-1 bg-[#e4e7ec] my-1" style={{ minHeight: 20 }} />
              )}
            </div>
            {/* Right column: content */}
            <div className="pb-4 min-w-0">
              <div className={`text-[12px] font-semibold uppercase tracking-wide ${s.text}`}>
                {step.label}
              </div>
              {step.detail && (
                <div className="text-[12px] text-[#94a3b8] mt-0.5">{step.detail}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Utility: build pipeline steps from an AgentRunResponse
import type { AgentRunResponse } from "@/lib/types";

export function buildPipelineSteps(result: AgentRunResponse | null, loading: boolean): PipelineStep[] {
  if (!result && !loading) return defaultSteps();
  if (loading) return activatingSteps();

  const g = result!.governance;
  const status = result!.status;

  const identityState: StepState = g.identity_verified ? "success" : "denied";
  const agentState: StepState = g.agent_id ? "success" : (status === "BLOCKED" ? "blocked" : "idle");
  const policyDecision = g.policy_decision?.toUpperCase() ?? "";
  const policyState: StepState = policyDecision.includes("ALLOW") ? "success"
    : policyDecision.includes("DENY") ? "denied"
    : policyDecision.includes("PENDING") ? "warning"
    : status === "BLOCKED" ? "blocked"
    : "idle";
  const riskState: StepState = g.risk_level ? "success" : (policyState === "denied" ? "denied" : "idle");
  const approvalState: StepState = status === "INTERRUPTED_PENDING_APPROVAL" ? "warning"
    : status === "COMPLETED" || status === "DENIED" ? "success"
    : "idle";
  const execState: StepState = status === "COMPLETED" ? "success"
    : status === "DENIED" ? "denied"
    : status === "BLOCKED" ? "blocked"
    : status === "INTERRUPTED_PENDING_APPROVAL" ? "idle"
    : "idle";
  const auditState: StepState = (status === "COMPLETED" || status === "DENIED" || status === "BLOCKED") ? "success" : "idle";

  return [
    { id: "identity", label: "Identity", state: identityState, detail: g.identity_verified ? "JWT verified" : "Unverified" },
    { id: "agent",    label: "Agent",    state: agentState,    detail: g.agent_id ?? undefined },
    { id: "policy",   label: "Policy",   state: policyState,   detail: g.policy_decision },
    { id: "risk",     label: "Risk",     state: riskState,     detail: g.risk_level ?? undefined },
    { id: "approval", label: "Approval", state: approvalState, detail: status === "INTERRUPTED_PENDING_APPROVAL" ? "Awaiting human review" : "Not required" },
    { id: "exec",     label: "Execution",state: execState,     detail: status === "COMPLETED" ? (g.execution_time_ms ? `${g.execution_time_ms.toFixed(0)}ms` : "Completed") : undefined },
    { id: "audit",    label: "Audit",    state: auditState,    detail: result!.trace_id },
  ];
}

function defaultSteps(): PipelineStep[] {
  return [
    { id: "identity", label: "Identity", state: "idle" },
    { id: "agent",    label: "Agent",    state: "idle" },
    { id: "policy",   label: "Policy",   state: "idle" },
    { id: "risk",     label: "Risk",     state: "idle" },
    { id: "approval", label: "Approval", state: "idle" },
    { id: "exec",     label: "Execution",state: "idle" },
    { id: "audit",    label: "Audit",    state: "idle" },
  ];
}

function activatingSteps(): PipelineStep[] {
  return [
    { id: "identity", label: "Identity", state: "active" },
    { id: "agent",    label: "Agent",    state: "idle" },
    { id: "policy",   label: "Policy",   state: "idle" },
    { id: "risk",     label: "Risk",     state: "idle" },
    { id: "approval", label: "Approval", state: "idle" },
    { id: "exec",     label: "Execution",state: "idle" },
    { id: "audit",    label: "Audit",    state: "idle" },
  ];
}

// Icons
function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2 6l3 3 5-5" stroke="#16a34a" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function XIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M3 3l6 6M9 3l-6 6" stroke="#dc2626" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}
function WarnIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 2l4.5 8H1.5L6 2z" stroke="#d97706" strokeWidth="1.2" strokeLinejoin="round"/>
      <path d="M6 5.5v2M6 8.5h.01" stroke="#d97706" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}
function BlockIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="4.5" stroke="#ea580c" strokeWidth="1.2"/>
      <path d="M3 9l6-6" stroke="#ea580c" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}
function CircleIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="4.5" stroke="#e4e7ec" strokeWidth="1.2"/>
    </svg>
  );
}
function SpinIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="animate-spin">
      <circle cx="6" cy="6" r="4.5" stroke="#c7d8fe" strokeWidth="1.2"/>
      <path d="M6 1.5A4.5 4.5 0 0110.5 6" stroke="#3b5bdb" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  );
}
