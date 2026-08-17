import type { AuditEvent } from "@/lib/types";
import { DecisionBadge, RiskBadge } from "@/components/ui/Badge";
import { fmtDateTime } from "@/lib/utils";

interface GovernanceTimelineProps {
  events: AuditEvent[];
}

export function GovernanceTimeline({ events }: GovernanceTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-slate-400 italic">No events for this trace.</p>
    );
  }

  return (
    <div className="relative">
      <div className="absolute left-3 top-3 bottom-3 w-px bg-slate-200" />
      <div className="space-y-4">
        {events.map((evt) => (
          <div key={evt.id} className="flex items-start gap-4">
            <div className="relative z-10 w-6 h-6 rounded-full bg-white border-2 border-slate-300 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono text-slate-500" suppressHydrationWarning>
                  {fmtDateTime(evt.createdAt)}
                </span>
                <DecisionBadge decision={evt.decision} />
                {evt.riskLevel && <RiskBadge risk={evt.riskLevel} />}
              </div>
              <p className="text-sm font-medium text-slate-800 mt-0.5">
                {evt.actionType}
              </p>
              <p className="text-xs text-slate-500">{evt.reason}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
