import { Topbar } from "@/components/layout/Topbar";
import { AGENTS } from "@/data/agents";

const ROLE_COLORS: Record<string, string> = {
  analyst: "bg-sky-50 text-sky-700 border-sky-200",
  billing: "bg-purple-50 text-purple-700 border-purple-200",
  admin: "bg-rose-50 text-rose-700 border-rose-200",
};

export default function AgentsPage() {
  return (
    <div>
      <Topbar
        title="Agent Registry"
        subtitle="Registered workload identities and their authorized tool capabilities"
      />

      <div className="p-6 space-y-4 max-w-3xl">
        {/* Authorization matrix */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Role → Agent Authorization Matrix
          </h3>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">
                    Role
                  </th>
                  {AGENTS.filter((a) => a.id !== "supervisor").map((a) => (
                    <th
                      key={a.id}
                      className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase"
                    >
                      {a.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(["analyst", "billing", "admin"] as const).map((role) => (
                  <tr key={role} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded border ${ROLE_COLORS[role]}`}
                      >
                        {role}
                      </span>
                    </td>
                    {AGENTS.filter((a) => a.id !== "supervisor").map((agent) => {
                      const allowed = agent.allowedRoles.includes(role);
                      return (
                        <td key={agent.id} className="px-4 py-3 text-center">
                          {allowed ? (
                            <span className="text-emerald-600 font-bold">✓</span>
                          ) : (
                            <span className="text-slate-300">✗</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Agent cards */}
        {AGENTS.map((agent) => (
          <div
            key={agent.id}
            className="bg-white border border-slate-200 rounded-xl p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-base font-semibold text-slate-900">
                  {agent.name}
                </div>
                <div className="font-mono text-xs text-slate-500 mt-0.5">
                  {agent.spiffeId}
                </div>
                <p className="text-sm text-slate-600 mt-2">{agent.description}</p>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-slate-500 mb-2">Tools</div>
                {agent.tools.length === 0 ? (
                  <div className="text-xs text-slate-400 italic">
                    No direct tool access
                  </div>
                ) : (
                  <div className="space-y-1">
                    {agent.tools.map((t) => (
                      <div
                        key={t}
                        className="font-mono text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded px-2 py-0.5 inline-block mr-1 mb-1"
                      >
                        {t}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-2">Allowed Roles</div>
                <div className="flex flex-wrap gap-1">
                  {agent.allowedRoles.map((r) => (
                    <span
                      key={r}
                      className={`text-xs font-semibold px-2 py-0.5 rounded border ${ROLE_COLORS[r]}`}
                    >
                      {r}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
