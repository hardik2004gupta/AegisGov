import type { GovernanceStep } from "@/lib/types";
import { stepStatusColor } from "@/lib/utils";

interface GovernancePipelineProps {
  steps: GovernanceStep[];
}

export function GovernancePipeline({ steps }: GovernancePipelineProps) {
  return (
    <div className="relative">
      {/* vertical connector line */}
      <div className="absolute left-4 top-4 bottom-4 w-px bg-slate-200" />

      <div className="space-y-1">
        {steps.map((step, i) => {
          const colors = stepStatusColor(step.status);
          return (
            <div key={step.id} className="flex items-start gap-4 pl-0">
              {/* step circle */}
              <div
                className={`relative z-10 w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 text-xs font-bold ${colors.bg} ${colors.border} ${colors.text} transition-all duration-300`}
              >
                {step.status === "running" ? (
                  <span className="animate-spin inline-block">◌</span>
                ) : (
                  colors.icon
                )}
              </div>

              {/* step content */}
              <div className="flex-1 pb-3 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-sm font-semibold ${step.status === "idle" || step.status === "skipped" ? "text-slate-400" : "text-slate-800"}`}
                  >
                    {step.label}
                  </span>
                  {step.durationMs && step.status !== "idle" && (
                    <span className="text-xs text-slate-400">
                      {step.durationMs}ms
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {step.description}
                </p>
                {step.detail && step.status !== "idle" && (
                  <div
                    className={`mt-1 text-xs font-mono px-2 py-1 rounded border ${colors.bg} ${colors.border} ${colors.text}`}
                  >
                    {step.detail}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
