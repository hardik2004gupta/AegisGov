import { Topbar } from "@/components/layout/Topbar";
import { RUNTIME_METRICS } from "@/data/runtime";
import { fmtNumber } from "@/lib/utils";

function Gauge({
  label,
  used,
  total,
  color,
}: {
  label: string;
  used: number;
  total: number;
  color: string;
}) {
  const pct = Math.round((used / total) * 100);
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="text-sm font-bold text-slate-900">
          {used}/{total}
        </span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="text-xs text-slate-400 mt-1">{pct}% of budget used</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  sub,
  color = "text-slate-900",
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm font-medium text-slate-700 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${d}d ${h}h ${m}m`;
}

export default function RuntimePage() {
  const m = RUNTIME_METRICS;
  const total = m.allowed + m.denied + m.blocked + m.pendingApprovals;

  return (
    <div>
      <Topbar
        title="Runtime Dashboard"
        subtitle="Live governance budget, throughput, and safety limits"
      />

      <div className="p-6 space-y-6 max-w-4xl">
        {/* overview */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Decision Overview
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Allowed"
              value={fmtNumber(m.allowed)}
              sub={`${Math.round((m.allowed / total) * 100)}%`}
              color="text-emerald-600"
            />
            <MetricCard
              label="Denied (OPA)"
              value={fmtNumber(m.denied)}
              sub={`${Math.round((m.denied / total) * 100)}%`}
              color="text-red-600"
            />
            <MetricCard
              label="Blocked"
              value={fmtNumber(m.blocked)}
              sub="injection + loops"
              color="text-orange-600"
            />
            <MetricCard
              label="Pending Approval"
              value={fmtNumber(m.pendingApprovals)}
              sub="awaiting human"
              color="text-amber-600"
            />
          </div>
        </div>

        {/* runtime budgets */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Runtime Safety Budgets (Current Request)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Gauge
              label="Tool Calls"
              used={m.toolCallsUsed}
              total={m.toolCallBudget}
              color="bg-blue-500"
            />
            <Gauge
              label="Agent Handoffs"
              used={m.handoffsUsed}
              total={m.handoffBudget}
              color="bg-purple-500"
            />
          </div>
        </div>

        {/* configured limits */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Configured Safety Limits
          </h3>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            {[
              {
                key: "max_tool_calls",
                value: m.toolCallBudget,
                desc: "Maximum tool calls per execution",
              },
              {
                key: "max_agent_handoffs",
                value: m.handoffBudget,
                desc: "Maximum supervisor → specialist handoffs",
              },
              {
                key: "max_identical_tool_calls",
                value: m.maxIdenticalCalls,
                desc: "Consecutive identical calls before loop detection",
              },
              {
                key: "max_execution_time",
                value: "60s",
                desc: "Maximum wall-clock time per request",
              },
              {
                key: "hitl_threshold_refund",
                value: "$500",
                desc: "Refund amount above which human approval is required",
              },
              {
                key: "critical_always_hitl",
                value: "true",
                desc: "CRITICAL risk tools always require human approval",
              },
            ].map((row) => (
              <div
                key={row.key}
                className="flex items-center justify-between px-5 py-3 border-b border-slate-100 last:border-0"
              >
                <div>
                  <div className="font-mono text-xs text-slate-700">
                    {row.key}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">{row.desc}</div>
                </div>
                <div className="font-mono text-sm font-semibold text-slate-900">
                  {row.value}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* performance + uptime */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Performance
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <MetricCard
              label="Avg Execution Time"
              value={`${m.avgExecutionMs}ms`}
              sub="per governed request"
            />
            <MetricCard
              label="Total Proposals"
              value={fmtNumber(m.totalProposals)}
              sub="lifetime"
            />
            <MetricCard
              label="Uptime"
              value={formatUptime(m.uptimeSeconds)}
              sub="since last restart"
            />
          </div>
        </div>

        {/* threat coverage table */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Threat Coverage
          </h3>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            {[
              {
                threat: "Prompt Injection",
                defense: "Input guardrails (graph node)",
                status: "ACTIVE",
              },
              {
                threat: "Unauthorized Tool",
                defense: "OPA + Tool Registry",
                status: "ACTIVE",
              },
              {
                threat: "Agent Privilege Escalation",
                defense: "Handoff authorization (OPA)",
                status: "ACTIVE",
              },
              {
                threat: "Excessive Agency",
                defense: "Tool call budget",
                status: "ACTIVE",
              },
              {
                threat: "Agent Loops",
                defense: "Repeated-call detection",
                status: "ACTIVE",
              },
              {
                threat: "Parameter Tampering",
                defense: "Pydantic validation",
                status: "ACTIVE",
              },
              {
                threat: "Sensitive Data Access",
                defense: "Least-privilege DB roles",
                status: "ACTIVE",
              },
              {
                threat: "Destructive Actions",
                defense: "HITL (human approval)",
                status: "ACTIVE",
              },
              {
                threat: "Unauthorized Human Role",
                defense: "Keycloak JWT verification",
                status: "ACTIVE",
              },
              {
                threat: "Unregistered Tool",
                defense: "Tool Registry (fail closed)",
                status: "ACTIVE",
              },
            ].map((row) => (
              <div
                key={row.threat}
                className="flex items-center justify-between px-5 py-3 border-b border-slate-100 last:border-0"
              >
                <div>
                  <div className="text-sm font-medium text-slate-800">
                    {row.threat}
                  </div>
                  <div className="text-xs text-slate-500">{row.defense}</div>
                </div>
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                  {row.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
