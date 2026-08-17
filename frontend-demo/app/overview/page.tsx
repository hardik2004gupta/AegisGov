import { Topbar } from "@/components/layout/Topbar";
import { RUNTIME_METRICS } from "@/data/runtime";
import { TOOLS } from "@/data/tools";
import { AGENTS } from "@/data/agents";
import { fmtNumber } from "@/lib/utils";

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm font-medium text-slate-700 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

export default function OverviewPage() {
  const m = RUNTIME_METRICS;
  const allowPct = Math.round((m.allowed / m.totalProposals) * 100);
  const denyPct = Math.round((m.denied / m.totalProposals) * 100);
  const blockPct = Math.round((m.blocked / m.totalProposals) * 100);

  return (
    <div>
      <Topbar
        title="AegisGov"
        subtitle="Zero-Trust Execution Gateway for Agentic AI"
      />

      <div className="p-6 space-y-8 max-w-5xl">
        {/* Hero */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 text-white">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">
                Architecture Invariant
              </div>
              <h2 className="text-2xl font-bold leading-tight">
                Agents propose actions.
                <br />
                <span className="text-blue-400">AegisGov owns execution authority.</span>
              </h2>
              <p className="text-slate-400 text-sm mt-3 max-w-xl leading-relaxed">
                Every tool call passes through human and agent identity
                verification, OPA policy authorization, runtime safety checks,
                strict schema validation, risk-based classification, and
                conditional human approval — before a single database row is
                touched.
              </p>
            </div>
            <div className="hidden md:flex flex-col gap-1 text-xs font-mono text-slate-500 flex-shrink-0">
              <span>aegis://agents/supervisor</span>
              <span>aegis://agents/order-agent</span>
              <span>aegis://agents/billing-agent</span>
              <span>aegis://agents/admin-agent</span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Lifetime Governance Decisions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard
              label="Total Proposals"
              value={fmtNumber(m.totalProposals)}
              color="text-slate-900"
            />
            <StatCard
              label="Allowed"
              value={fmtNumber(m.allowed)}
              sub={`${allowPct}%`}
              color="text-emerald-600"
            />
            <StatCard
              label="Denied"
              value={fmtNumber(m.denied)}
              sub={`${denyPct}%`}
              color="text-red-600"
            />
            <StatCard
              label="Blocked"
              value={fmtNumber(m.blocked)}
              sub={`${blockPct}%`}
              color="text-orange-600"
            />
            <StatCard
              label="Pending Approval"
              value={fmtNumber(m.pendingApprovals)}
              color="text-amber-600"
            />
          </div>
        </div>

        {/* Trust Boundary Pipeline */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Governance Pipeline (Every Request)
          </h3>
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex flex-wrap gap-2 items-center text-sm">
              {[
                { label: "Identity\nVerification", color: "bg-blue-100 text-blue-800 border-blue-200" },
                { label: "Input\nGuardrails", color: "bg-purple-100 text-purple-800 border-purple-200" },
                { label: "Supervisor\nRouter", color: "bg-slate-100 text-slate-700 border-slate-200" },
                { label: "Handoff\nAuthorization", color: "bg-orange-100 text-orange-800 border-orange-200" },
                { label: "Runtime\nLimits", color: "bg-yellow-100 text-yellow-800 border-yellow-200" },
                { label: "Pydantic\nValidation", color: "bg-indigo-100 text-indigo-800 border-indigo-200" },
                { label: "OPA Tool\nAuthorization", color: "bg-orange-100 text-orange-800 border-orange-200" },
                { label: "Risk\nClassification", color: "bg-red-100 text-red-800 border-red-200" },
                { label: "HITL / Secure\nExecution", color: "bg-emerald-100 text-emerald-800 border-emerald-200" },
                { label: "Audit\nTrail", color: "bg-slate-100 text-slate-700 border-slate-200" },
              ].map((step, i, arr) => (
                <div key={i} className="flex items-center gap-2">
                  <div
                    className={`px-3 py-2 rounded-lg border text-xs font-medium text-center whitespace-pre-line leading-tight ${step.color}`}
                  >
                    {step.label}
                  </div>
                  {i < arr.length - 1 && (
                    <span className="text-slate-400 text-sm">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 8 Invariants */}
        <div>
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Architecture Invariants
          </h3>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            {[
              "Direct Agent → Tool calls are FORBIDDEN",
              "Frontend → Authorization derivation is FORBIDDEN",
              "LLM → Final policy decision is FORBIDDEN",
              "OPA unavailable → ALLOW is FORBIDDEN",
              "CRITICAL action → automatic execution is FORBIDDEN",
              "Invalid parameters → handler execution is FORBIDDEN",
              "Unregistered tool → execution is FORBIDDEN",
              "Rejected approval → database mutation is FORBIDDEN",
            ].map((inv, i) => (
              <div
                key={i}
                className="flex items-start gap-3 px-5 py-3 border-b border-slate-100 last:border-0"
              >
                <span className="text-xs font-mono text-slate-400 flex-shrink-0 mt-0.5">
                  INV-{i + 1}
                </span>
                <span className="text-sm text-slate-700">{inv}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Governed tools and agents summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Governed Tools
            </h3>
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              {TOOLS.map((tool) => (
                <div
                  key={tool.name}
                  className="flex items-center justify-between px-4 py-3 border-b border-slate-100 last:border-0"
                >
                  <span className="font-mono text-xs text-slate-700">
                    {tool.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded border font-medium ${
                        tool.risk === "LOW"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : tool.risk === "MEDIUM"
                            ? "bg-sky-50 text-sky-700 border-sky-200"
                            : tool.risk === "HIGH"
                              ? "bg-orange-50 text-orange-700 border-orange-200"
                              : "bg-red-50 text-red-700 border-red-200"
                      }`}
                    >
                      {tool.risk}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Agent Topology
            </h3>
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              {AGENTS.map((agent) => (
                <div
                  key={agent.id}
                  className="px-4 py-3 border-b border-slate-100 last:border-0"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-800">
                      {agent.name}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      {agent.tools.length} tool
                      {agent.tools.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-500 mt-0.5">
                    {agent.spiffeId}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Roles:{" "}
                    <span className="font-medium">
                      {agent.allowedRoles.join(", ")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
