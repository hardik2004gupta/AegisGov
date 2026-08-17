import type { Agent } from "@/lib/types";

export const AGENTS: Agent[] = [
  {
    id: "supervisor",
    name: "Supervisor",
    spiffeId: "aegis://agents/supervisor",
    tools: [],
    allowedRoles: ["analyst", "billing", "admin"],
    description:
      "Understands user intent, selects the appropriate specialist, and requests an authorized handoff via OPA. Never directly executes privileged tools.",
  },
  {
    id: "order-agent",
    name: "Order Agent",
    spiffeId: "aegis://agents/order-agent",
    tools: ["get_order", "get_customer"],
    allowedRoles: ["analyst", "billing", "admin"],
    description:
      "Handles order and customer data retrieval for all authorized users.",
  },
  {
    id: "billing-agent",
    name: "Billing Agent",
    spiffeId: "aegis://agents/billing-agent",
    tools: ["get_order", "get_payment", "issue_refund"],
    allowedRoles: ["billing", "admin"],
    description:
      "Handles payment lookups and refund issuance. Restricted to billing and admin roles.",
  },
  {
    id: "admin-agent",
    name: "Admin Agent",
    spiffeId: "aegis://agents/admin-agent",
    tools: ["get_customer", "delete_customer"],
    allowedRoles: ["admin"],
    description:
      "Handles destructive administrative operations. Restricted to admin role only.",
  },
];
