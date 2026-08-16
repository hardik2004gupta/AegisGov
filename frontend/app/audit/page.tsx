// Audit Explorer — Phase 5 implements the live audit view.
//
// Displays all governance decisions from PostgreSQL audit_events table.
// Every important request has a full record (CLAUDE.md §33):
//   trace_id, user, agent, tool, decision, risk, reason, timestamp
//
// Backed by: GET /api/v1/audit
//            GET /api/v1/audit/{trace_id}

const COLUMNS = [
  "Timestamp",
  "Trace ID",
  "User",
  "Agent",
  "Tool",
  "Decision",
  "Risk",
  "Reason",
];

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-lg font-semibold text-slate-100">Audit Explorer</h1>
        <p className="text-sm text-slate-500 mt-1">
          Complete immutable record of every governance decision.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-slate-400">
          <thead>
            <tr className="border-b border-slate-800">
              {COLUMNS.map((col) => (
                <th
                  key={col}
                  className="text-left py-2 px-3 text-slate-600 uppercase tracking-wider font-normal"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td
                colSpan={COLUMNS.length}
                className="py-8 text-center text-slate-700 italic"
              >
                Audit events surface in Phase 4. Schema and indexes ready.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
