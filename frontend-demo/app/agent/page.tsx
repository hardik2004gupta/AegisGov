"use client";

import { useState, useCallback } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { GovernancePipeline } from "@/components/governance/GovernancePipeline";
import { DecisionBadge, RiskBadge } from "@/components/ui/Badge";
import { SCENARIOS } from "@/data/scenarios";
import { runAgentScenario } from "@/lib/mock-api";
import type { GovernanceStep, AgentRunResult, Scenario, StepStatus } from "@/lib/types";

type RunState = "idle" | "running" | "done";

export default function AgentConsolePage() {
  const [selectedId, setSelectedId] = useState<string>(SCENARIOS[0].id);
  const [runState, setRunState] = useState<RunState>("idle");
  const [steps, setSteps] = useState<GovernanceStep[]>([]);
  const [result, setResult] = useState<AgentRunResult | null>(null);

  const scenario: Scenario = SCENARIOS.find((s) => s.id === selectedId)!;

  const initSteps = useCallback(
    (sc: Scenario): GovernanceStep[] =>
      sc.steps.map((s) => ({
        id: s.id,
        label: s.label,
        description: s.description,
        status: "idle" as const,
      })),
    []
  );

  const handleRun = useCallback(async () => {
    setRunState("running");
    setResult(null);
    setSteps(initSteps(scenario));

    const res = await runAgentScenario(scenario.id, (index, status, detail) => {
      setSteps((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], status: status as StepStatus, detail };
        return next;
      });
    });

    setResult(res);
    setRunState("done");
  }, [scenario, initSteps]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setRunState("idle");
    setResult(null);
    setSteps([]);
  };

  const statusColor: Record<string, string> = {
    COMPLETED: "text-emerald-700 bg-emerald-50 border-emerald-200",
    DENIED: "text-red-700 bg-red-50 border-red-200",
    BLOCKED: "text-orange-700 bg-orange-50 border-orange-200",
    INTERRUPTED_PENDING_APPROVAL:
      "text-amber-700 bg-amber-50 border-amber-200",
  };

  return (
    <div>
      <Topbar
        title="Agent Console"
        subtitle="Run governed scenarios and observe every governance decision"
      />

      <div className="p-6">
        <div className="flex gap-6">
          {/* scenario list */}
          <div className="w-64 flex-shrink-0 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
              Demo Scenarios
            </p>
            {SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => handleSelect(sc.id)}
                disabled={runState === "running"}
                className={`w-full text-left px-3 py-3 rounded-xl border text-sm transition-all ${
                  selectedId === sc.id
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-slate-700 border-slate-200 hover:border-blue-300 hover:bg-blue-50"
                } disabled:opacity-50`}
              >
                <div className="font-medium leading-tight">{sc.title}</div>
                <div
                  className={`text-xs mt-1 ${selectedId === sc.id ? "text-blue-200" : "text-slate-500"}`}
                >
                  {sc.userRole} · {sc.riskLevel}
                </div>
              </button>
            ))}
          </div>

          {/* main panel */}
          <div className="flex-1 min-w-0 space-y-4">
            {/* scenario header */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold text-slate-900">
                    {scenario.title}
                  </h2>
                  <p className="text-sm text-slate-500 mt-1">
                    {scenario.description}
                  </p>
                </div>
                <button
                  onClick={handleRun}
                  disabled={runState === "running"}
                  className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {runState === "running" ? "Running…" : "Run Scenario"}
                </button>
              </div>

              <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t border-slate-100">
                <div>
                  <span className="text-xs text-slate-500">User</span>
                  <div className="text-sm font-medium text-slate-800 mt-0.5">
                    {scenario.userRole}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Agent</span>
                  <div className="text-sm font-mono text-slate-800 mt-0.5">
                    {scenario.agentId}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Tool</span>
                  <div className="text-sm font-mono text-slate-800 mt-0.5">
                    {scenario.toolName}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Risk</span>
                  <div className="mt-0.5">
                    <RiskBadge risk={scenario.riskLevel} />
                  </div>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Expected</span>
                  <div className="mt-0.5">
                    <DecisionBadge decision={scenario.expectedDecision} />
                  </div>
                </div>
              </div>

              {/* tool args */}
              {Object.keys(scenario.toolArgs).length > 0 && (
                <div className="mt-3">
                  <span className="text-xs text-slate-500">
                    Tool Arguments
                  </span>
                  <div className="mt-1 font-mono text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700">
                    {JSON.stringify(scenario.toolArgs, null, 2)}
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* pipeline */}
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-700 mb-4">
                  Governance Pipeline
                </h3>
                {steps.length === 0 ? (
                  <div className="text-sm text-slate-400 italic">
                    Click &ldquo;Run Scenario&rdquo; to start.
                  </div>
                ) : (
                  <GovernancePipeline steps={steps} />
                )}
              </div>

              {/* result */}
              <div className="space-y-4">
                {result ? (
                  <>
                    {/* status */}
                    <div
                      className={`rounded-xl p-4 border ${statusColor[result.status] ?? "bg-slate-50 border-slate-200 text-slate-700"}`}
                    >
                      <div className="text-xs font-semibold uppercase tracking-wider opacity-70 mb-1">
                        Final Status
                      </div>
                      <div className="font-bold text-lg">{result.status}</div>
                      <div className="text-sm mt-2 opacity-90">
                        {result.output}
                      </div>
                    </div>

                    {/* governance summary */}
                    <div className="bg-white border border-slate-200 rounded-xl p-4">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                        Governance Summary
                      </h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <div className="text-slate-500 text-xs">Identity</div>
                          <div className="font-medium text-emerald-700">
                            {result.governance.identityVerified
                              ? "Verified"
                              : "Failed"}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500 text-xs">
                            Policy Decision
                          </div>
                          <DecisionBadge
                            decision={result.governance.policyDecision}
                          />
                        </div>
                        <div>
                          <div className="text-slate-500 text-xs">
                            Risk Level
                          </div>
                          <RiskBadge risk={result.governance.riskLevel} />
                        </div>
                        <div>
                          <div className="text-slate-500 text-xs">
                            Execution Time
                          </div>
                          <div className="font-medium text-slate-800">
                            {result.governance.executionTimeMs}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500 text-xs">
                            Agent
                          </div>
                          <div className="font-mono text-xs text-slate-700">
                            {result.governance.agentId}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-500 text-xs">
                            Steps
                          </div>
                          <div className="font-medium text-slate-800">
                            {result.governance.stepsCompleted}/
                            {result.steps.length}
                          </div>
                        </div>
                      </div>

                      {result.traceId && (
                        <div className="mt-3 pt-3 border-t border-slate-100">
                          <div className="text-slate-500 text-xs mb-1">
                            Trace ID
                          </div>
                          <div className="font-mono text-xs text-slate-600 bg-slate-50 rounded px-2 py-1">
                            {result.traceId}
                          </div>
                        </div>
                      )}

                      {result.approvalId && (
                        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <div className="text-xs font-semibold text-amber-800 mb-1">
                            Approval Required
                          </div>
                          <div className="font-mono text-xs text-amber-700">
                            {result.approvalId}
                          </div>
                          <div className="text-xs text-amber-700 mt-1">
                            Go to Approval Queue to resolve.
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-sm text-slate-400">
                    {runState === "running"
                      ? "Executing governance pipeline…"
                      : "Results will appear here."}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
