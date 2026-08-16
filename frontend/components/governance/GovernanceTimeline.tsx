"use client";

import type { AuditEvent } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

const ACTION_LABELS: Record<string, { label: string; icon: string }> = {
  IDENTITY_VERIFIED:      { label: "Identity Verified",      icon: "🔐" },
  IDENTITY_DENIED:        { label: "Identity Denied",        icon: "🔐" },
  INPUT_BLOCKED:          { label: "Input Blocked",          icon: "🛡️" },
  INPUT_ACCEPTED:         { label: "Input Accepted",         icon: "✓" },
  AGENT_HANDOFF_ALLOWED:  { label: "Agent Handoff Allowed",  icon: "→" },
  AGENT_HANDOFF_DENIED:   { label: "Agent Handoff Denied",   icon: "✕" },
  TOOL_PROPOSAL_CREATED:  { label: "Tool Proposal",         icon: "📋" },
  TOOL_UNKNOWN:           { label: "Unknown Tool",           icon: "✕" },
  TOOL_VALIDATION_DENIED: { label: "Validation Failed",     icon: "✕" },
  RUNTIME_LIMIT_BLOCKED:  { label: "Runtime Limit",         icon: "⚠" },
  POLICY_ALLOWED:         { label: "Policy Allowed",        icon: "✓" },
  POLICY_DENIED:          { label: "Policy Denied",         icon: "✕" },
  RISK_CLASSIFIED:        { label: "Risk Classified",       icon: "⚑" },
  APPROVAL_CREATED:       { label: "Approval Created",      icon: "⏸" },
  APPROVAL_APPROVED:      { label: "Approval Approved",     icon: "✓" },
  APPROVAL_REJECTED:      { label: "Approval Rejected",     icon: "✕" },
  TOOL_EXECUTION_STARTED: { label: "Execution Started",     icon: "▶" },
  TOOL_EXECUTION_COMPLETED:{ label: "Execution Completed",  icon: "✓" },
  TOOL_EXECUTION_FAILED:  { label: "Execution Failed",      icon: "✕" },
  TOOL_RESULT_SANITIZED:  { label: "Result Sanitized",      icon: "🔒" },
};

function fmtTime(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  } catch {
    return iso;
  }
}

interface GovernanceTimelineProps {
  events: AuditEvent[];
}

export function GovernanceTimeline({ events }: GovernanceTimelineProps) {
  if (events.length === 0) {
    return <div className="text-[13px] text-[#94a3b8] text-center py-8">No events for this trace.</div>;
  }

  return (
    <div className="space-y-0">
      {events.map((evt, i) => {
        const meta = ACTION_LABELS[evt.action_type] ?? { label: evt.action_type, icon: "·" };
        const isLast = i === events.length - 1;

        return (
          <div key={evt.id} className="flex gap-3">
            {/* Left: icon + connector */}
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-white border border-[#e4e7ec] flex items-center justify-center flex-shrink-0 text-[11px] shadow-sm">
                {meta.icon}
              </div>
              {!isLast && (
                <div className="w-px flex-1 bg-[#e4e7ec] my-1" style={{ minHeight: 16 }} />
              )}
            </div>

            {/* Right: content */}
            <div className="pb-4 min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] text-[#94a3b8] font-mono tabular">{fmtTime(evt.created_at)}</span>
                <span className="text-[13px] font-medium text-[#0f172a]">{meta.label}</span>
                <Badge value={evt.decision} showDot />
              </div>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                {evt.agent_id && evt.agent_id !== "system" && (
                  <span className="text-[11px] text-[#94a3b8] font-mono">{evt.agent_id}</span>
                )}
                {evt.user_id && evt.user_id !== "system" && (
                  <span className="text-[11px] text-[#94a3b8]">{evt.user_id}</span>
                )}
              </div>
              {evt.reason && (
                <div className="text-[12px] text-[#475569] mt-1">{evt.reason}</div>
              )}
              {Object.keys(evt.payload ?? {}).length > 0 && (
                <details className="mt-1">
                  <summary className="text-[11px] text-[#94a3b8] cursor-pointer hover:text-[#475569]">
                    Payload
                  </summary>
                  <pre className="mt-1 text-[10px] text-[#475569] bg-[#f7f8fa] border border-[#e4e7ec] rounded p-2 overflow-x-auto">
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
