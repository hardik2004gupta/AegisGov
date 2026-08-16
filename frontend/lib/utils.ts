export function fmtTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    });
  } catch { return iso; }
}

export function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false,
    });
  } catch { return iso; }
}

export function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const s = Math.floor(diff / 1000);
    if (s < 60)  return `${s}s ago`;
    const m = Math.floor(s / 60);
    if (m < 60)  return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24)  return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  } catch { return iso; }
}

export function truncate(str: string, len: number): string {
  return str.length > len ? str.slice(0, len) + "…" : str;
}

export function agentDisplayName(agentId: string): string {
  const map: Record<string, string> = {
    "supervisor":     "Supervisor",
    "order-agent":    "Order Agent",
    "billing-agent":  "Billing Agent",
    "admin-agent":    "Admin Agent",
    "system":         "System",
  };
  return map[agentId] ?? agentId;
}

export function agentSpiffeLabel(spiffe: string): string {
  return spiffe.replace("aegis://agents/", "aegis://…/");
}
