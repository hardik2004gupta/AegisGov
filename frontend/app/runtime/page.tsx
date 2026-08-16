// Runtime Dashboard — Phase 5 implements live metrics.
//
// Displays runtime governance budget utilization per thread:
//   Tool Calls    / max_tool_calls (8)
//   Agent Handoffs / max_agent_handoffs (4)
//   Execution Time / max_execution_time (60s)
//
// Aggregate stats across all threads:
//   Total tool calls | Allowed | Denied | Blocked | Pending Approvals
//
// Backed by: GET /api/v1/runtime/status

const STATS = [
  { label: "Tool Calls", value: "—", limit: "/ 8 max" },
  { label: "Allowed", value: "—", limit: "" },
  { label: "Denied", value: "—", limit: "" },
  { label: "Blocked", value: "—", limit: "(injection / loop)" },
  { label: "Pending Approvals", value: "—", limit: "" },
];

export default function RuntimePage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-lg font-semibold text-slate-100">Runtime Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time governance budget and execution metrics.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {STATS.map((stat) => (
          <div
            key={stat.label}
            className="bg-slate-900 border border-slate-800 rounded-lg p-4"
          >
            <div className="text-2xl font-bold text-slate-600">{stat.value}</div>
            <div className="text-xs text-slate-500 mt-1">{stat.label}</div>
            {stat.limit && (
              <div className="text-xs text-slate-700 mt-0.5">{stat.limit}</div>
            )}
          </div>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">
          Budget Utilization
        </div>
        <div className="space-y-3">
          {[
            { label: "Tool Calls", used: 0, max: 8 },
            { label: "Agent Handoffs", used: 0, max: 4 },
          ].map((budget) => (
            <div key={budget.label}>
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>{budget.label}</span>
                <span>
                  {budget.used} / {budget.max}
                </span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full">
                <div className="h-full bg-aegis-600/40 rounded-full w-0" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="text-sm text-slate-600 italic">
        Live metrics implemented in Phase 5. Runtime limits configured in Phase 3.
      </div>
    </div>
  );
}
