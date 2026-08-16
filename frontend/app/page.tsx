// Agent Console — Phase 5 implements the live governance view.
//
// This view will display:
//   - User identity and role (from Keycloak JWT)
//   - Active specialist agent
//   - Proposed tool and arguments
//   - Risk level
//   - OPA policy decision
//   - Execution status
//   - Full governance timeline per request

export default function AgentConsolePage() {
  return (
    <div className="space-y-6">
      {/* ── Page header ── */}
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-lg font-semibold text-slate-100">Agent Console</h1>
        <p className="text-sm text-slate-500 mt-1">
          Live governance view — every tool call and policy decision, visible in real time.
        </p>
      </div>

      {/* ── Trust boundary reminder ── */}
      <div className="bg-aegis-900/40 border border-aegis-500/20 rounded-lg p-4 text-xs font-mono text-slate-400 space-y-1">
        <div className="text-aegis-500 font-semibold mb-2">TRUST BOUNDARY</div>
        <div>UNTRUSTED  →  User  →  LLM/Agent  →  Proposed Action</div>
        <div className="text-slate-600">══════════════════════════════════════</div>
        <div className="text-green-400">TRUSTED    →  AegisGov Gateway</div>
        <div className="pl-4 text-slate-500">
          Identity · OPA Policy · Pydantic · Risk · HITL · Audit
        </div>
        <div className="text-slate-600">══════════════════════════════════════</div>
        <div>AUTHORIZED →  Secure Tool  →  PostgreSQL</div>
      </div>

      {/* ── Placeholder panels ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Identity</div>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="flex justify-between">
              <span>User</span>
              <span className="text-slate-600">Phase 2</span>
            </div>
            <div className="flex justify-between">
              <span>Role</span>
              <span className="text-slate-600">Phase 2</span>
            </div>
            <div className="flex justify-between">
              <span>Agent</span>
              <span className="text-slate-600">Phase 2</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Tool Proposal</div>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="flex justify-between">
              <span>Tool</span>
              <span className="text-slate-600">Phase 3</span>
            </div>
            <div className="flex justify-between">
              <span>Risk</span>
              <span className="text-slate-600">Phase 3</span>
            </div>
            <div className="flex justify-between">
              <span>OPA Decision</span>
              <span className="text-slate-600">Phase 3</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Execution</div>
          <div className="space-y-2 text-sm text-slate-400">
            <div className="flex justify-between">
              <span>Status</span>
              <span className="text-slate-600">Phase 4</span>
            </div>
            <div className="flex justify-between">
              <span>Trace ID</span>
              <span className="text-slate-600">Phase 4</span>
            </div>
            <div className="flex justify-between">
              <span>Duration</span>
              <span className="text-slate-600">Phase 4</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Message</div>
        <div className="text-sm text-slate-600 italic">
          Full agent console implemented in Phase 5. Infrastructure ready.
        </div>
      </div>
    </div>
  );
}
