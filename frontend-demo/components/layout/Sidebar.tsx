"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DEMO_USER } from "@/data/users";

const NAV = [
  { href: "/overview", label: "Overview", icon: "◈" },
  { href: "/agent", label: "Agent Console", icon: "⬡" },
  { href: "/approvals", label: "Approval Queue", icon: "⊛", badge: 4 },
  { href: "/audit", label: "Audit Explorer", icon: "≡" },
  { href: "/runtime", label: "Runtime Dashboard", icon: "◎" },
];

const REGISTRY = [
  { href: "/tools", label: "Tool Registry", icon: "⚙" },
  { href: "/agents", label: "Agent Registry", icon: "⬡" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 flex-shrink-0 bg-slate-900 text-slate-300 flex flex-col h-screen sticky top-0">
      {/* logo */}
      <div className="px-4 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
            A
          </div>
          <div>
            <div className="text-sm font-semibold text-white leading-none">
              AegisGov
            </div>
            <div className="text-xs text-slate-500 mt-0.5">Governance Demo</div>
          </div>
        </div>
      </div>

      {/* main nav */}
      <nav className="px-2 py-3 flex-1 overflow-y-auto">
        <p className="px-2 pb-1 text-xs font-semibold uppercase tracking-wider text-slate-600">
          Governance
        </p>
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-2 py-2 rounded-md text-sm mb-0.5 transition-colors ${
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <span className="text-base w-4 text-center">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="bg-amber-500 text-white text-xs rounded-full px-1.5 py-0.5 leading-none font-medium">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <p className="px-2 pb-1 pt-4 text-xs font-semibold uppercase tracking-wider text-slate-600">
          Registry
        </p>
        {REGISTRY.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-2 py-2 rounded-md text-sm mb-0.5 transition-colors ${
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <span className="text-base w-4 text-center">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-blue-700 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
            {DEMO_USER.name[0]}
          </div>
          <div className="min-w-0">
            <div className="text-xs font-medium text-slate-300 truncate">
              {DEMO_USER.name}
            </div>
            <div className="text-xs text-slate-600 uppercase">{DEMO_USER.role}</div>
          </div>
        </div>
        <div className="mt-2 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
          <span className="text-xs text-slate-600">Demo Environment</span>
        </div>
      </div>
    </aside>
  );
}
