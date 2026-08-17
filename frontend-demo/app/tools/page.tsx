import { Topbar } from "@/components/layout/Topbar";
import { RiskBadge } from "@/components/ui/Badge";
import { TOOLS } from "@/data/tools";

export default function ToolsPage() {
  return (
    <div>
      <Topbar
        title="Tool Registry"
        subtitle="Authoritative list of executable governed tools — unregistered tools fail closed"
      />

      <div className="p-6 space-y-4 max-w-3xl">
        {TOOLS.map((tool) => (
          <div
            key={tool.name}
            className="bg-white border border-slate-200 rounded-xl p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-base font-semibold text-slate-900">
                    {tool.name}
                  </span>
                  <RiskBadge risk={tool.risk} />
                </div>
                <p className="text-sm text-slate-600 mt-1">{tool.description}</p>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-xs text-slate-500 mb-1">HITL Required</div>
                <div
                  className={`font-medium ${
                    tool.requiresApproval === true
                      ? "text-red-600"
                      : tool.requiresApproval === "conditional"
                        ? "text-amber-600"
                        : "text-emerald-600"
                  }`}
                >
                  {tool.requiresApproval === true
                    ? "Always"
                    : tool.requiresApproval === "conditional"
                      ? `Conditional`
                      : "Never"}
                </div>
                {tool.approvalCondition && (
                  <div className="text-xs text-slate-500 mt-0.5">
                    {tool.approvalCondition}
                  </div>
                )}
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">DB Role</div>
                <div className="font-mono text-xs text-slate-700">
                  {tool.dbRole}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Agents</div>
                <div className="space-y-0.5">
                  {tool.agents.map((a) => (
                    <div key={a} className="font-mono text-xs text-slate-600">
                      {a}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="text-xs text-slate-500 mb-2">Input Schema</div>
              <div className="font-mono text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700">
                {Object.entries(tool.schema).map(([k, v]) => (
                  <div key={k}>
                    <span className="text-blue-700">{k}</span>
                    <span className="text-slate-400">: </span>
                    <span className="text-emerald-700">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
