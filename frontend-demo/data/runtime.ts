import type { RuntimeMetrics } from "@/lib/types";

export const RUNTIME_METRICS: RuntimeMetrics = {
  totalProposals: 42381,
  allowed: 31204,
  denied: 6482,
  blocked: 3117,
  pendingApprovals: 1578,
  avgExecutionMs: 118,
  toolCallBudget: 8,
  toolCallsUsed: 3,
  handoffBudget: 4,
  handoffsUsed: 1,
  maxIdenticalCalls: 3,
  uptimeSeconds: 86400 * 12 + 3600 * 7 + 1800,
  lastUpdated: new Date().toISOString(),
};
