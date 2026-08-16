// Approval Queue — Phase 5 implements the live HITL approval UI.
//
// This view will display pending human approval requests for:
//   - CRITICAL operations (delete_customer — always requires approval)
//   - HIGH-value refunds (issue_refund > $500)
//
// Each row shows: tool, resource, agent, user, risk, reason, timestamp
// Actions: [ Approve ] [ Reject ]
//
// Backed by: GET /api/v1/governance/approvals
//            POST /api/v1/governance/approvals/{id}/resolve

export default function ApprovalsPage() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-lg font-semibold text-slate-100">Approval Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Pending human approval for CRITICAL operations and high-value transactions.
        </p>
      </div>

      <div className="bg-slate-900 border border-amber-700/30 rounded-lg p-4">
        <div className="text-xs text-amber-600 uppercase tracking-wider mb-3 flex items-center gap-2">
          <span>⬛</span>
          <span>CRITICAL — Pending Approval</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-400">
          <div>
            <div className="text-xs text-slate-600 mb-1">Tool</div>
            <div className="text-slate-600 italic">Phase 3</div>
          </div>
          <div>
            <div className="text-xs text-slate-600 mb-1">Resource</div>
            <div className="text-slate-600 italic">Phase 3</div>
          </div>
          <div>
            <div className="text-xs text-slate-600 mb-1">Requested by</div>
            <div className="text-slate-600 italic">Phase 3</div>
          </div>
          <div>
            <div className="text-xs text-slate-600 mb-1">Risk</div>
            <div className="text-red-900/60 text-xs px-2 py-0.5 rounded border border-red-800/40 inline-block">
              CRITICAL
            </div>
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <button
            disabled
            className="px-4 py-1.5 text-xs bg-green-900/20 border border-green-700/30 text-green-600/40 rounded cursor-not-allowed"
          >
            Approve
          </button>
          <button
            disabled
            className="px-4 py-1.5 text-xs bg-red-900/20 border border-red-700/30 text-red-600/40 rounded cursor-not-allowed"
          >
            Reject
          </button>
        </div>
      </div>

      <div className="text-sm text-slate-600 italic">
        Full approval workflow implemented in Phase 5. HITL persistence ready in Phase 3.
      </div>
    </div>
  );
}
