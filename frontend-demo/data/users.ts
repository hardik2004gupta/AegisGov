import type { User } from "@/lib/types";

export const DEMO_USER: User = {
  id: "usr_001",
  name: "Hardik Gupta",
  role: "admin",
  sub: "auth|hardik_gupta_001",
};

export const DEMO_USERS: User[] = [
  { id: "usr_001", name: "Hardik Gupta", role: "admin", sub: "auth|hardik_001" },
  { id: "usr_002", name: "Priya Sharma", role: "billing", sub: "auth|priya_002" },
  { id: "usr_003", name: "Rohan Verma", role: "analyst", sub: "auth|rohan_003" },
];
