"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/overview",   label: "Overview",       icon: OverviewIcon   },
  { href: "/agent",      label: "Agent Console",  icon: AgentIcon      },
  { href: "/approvals",  label: "Approvals",      icon: ApprovalsIcon  },
  { href: "/audit",      label: "Audit Explorer", icon: AuditIcon      },
  { href: "/runtime",    label: "Runtime",         icon: RuntimeIcon    },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>AegisGov</title>
        <meta name="description" content="Zero-Trust Execution Gateway for Agentic AI" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-[#f7f8fa]">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="w-56 flex-shrink-0 bg-white border-r border-[#e4e7ec] flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-[#e4e7ec]">
          <div className="flex items-center gap-2.5">
            <AegisLogo />
            <div>
              <div className="text-[13px] font-bold text-[#0f172a] tracking-tight">AegisGov</div>
              <div className="text-[10px] text-[#94a3b8] leading-tight">Zero-Trust Gateway</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = path === href || (href === "/overview" && path === "/");
            return (
              <Link
                key={href}
                href={href}
                className={[
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150",
                  active
                    ? "bg-[#e0e9ff] text-[#3b5bdb]"
                    : "text-[#475569] hover:bg-[#f7f8fa] hover:text-[#0f172a]",
                ].join(" ")}
                aria-current={active ? "page" : undefined}
              >
                <Icon active={active} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="px-4 py-4 border-t border-[#e4e7ec]">
          <div className="text-[11px] text-[#94a3b8]">v0.1.0</div>
          <div className="text-[10px] text-[#cbd5e1] mt-0.5 leading-tight">
            Agents propose.<br />AegisGov decides.
          </div>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-14 flex-shrink-0 bg-white border-b border-[#e4e7ec] flex items-center justify-between px-6">
          <div className="text-[13px] text-[#94a3b8]">
            {NAV.find(n => n.href === path || (path === "/" && n.href === "/overview"))?.label ?? "AegisGov"}
          </div>
          <div className="flex items-center gap-4">
            <HealthDot />
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[#e0e9ff] flex items-center justify-center text-[11px] font-semibold text-[#3b5bdb]">
                H
              </div>
              <div className="text-right">
                <div className="text-[12px] font-medium text-[#0f172a]">Demo User</div>
                <div className="text-[10px] text-[#94a3b8]">admin</div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[1200px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function HealthDot() {
  return (
    <div className="flex items-center gap-1.5 text-[11px] text-[#475569]">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
      Systems operational
    </div>
  );
}

function AegisLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 2L3 7.5V15c0 5.5 4.8 10.6 11 12 6.2-1.4 11-6.5 11-12V7.5L14 2z" fill="#3b5bdb" fillOpacity="0.12" stroke="#3b5bdb" strokeWidth="1.5" strokeLinejoin="round"/>
      <path d="M9 14l3.5 3.5L19 11" stroke="#3b5bdb" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

// Nav icons
function OverviewIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className={active ? "text-[#3b5bdb]" : "text-[#94a3b8]"}>
      <rect x="1" y="1" width="5.5" height="5.5" rx="1" fill="currentColor" fillOpacity="0.8"/>
      <rect x="8.5" y="1" width="5.5" height="5.5" rx="1" fill="currentColor" fillOpacity="0.5"/>
      <rect x="1" y="8.5" width="5.5" height="5.5" rx="1" fill="currentColor" fillOpacity="0.5"/>
      <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1" fill="currentColor" fillOpacity="0.8"/>
    </svg>
  );
}
function AgentIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className={active ? "text-[#3b5bdb]" : "text-[#94a3b8]"}>
      <circle cx="7.5" cy="5" r="3" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M2 13c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  );
}
function ApprovalsIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className={active ? "text-[#3b5bdb]" : "text-[#94a3b8]"}>
      <rect x="1.5" y="1.5" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M5 7.5l2 2 3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function AuditIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className={active ? "text-[#3b5bdb]" : "text-[#94a3b8]"}>
      <path d="M3 3h9M3 7h9M3 11h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
      <circle cx="12" cy="11" r="2.5" stroke="currentColor" strokeWidth="1.2"/>
    </svg>
  );
}
function RuntimeIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className={active ? "text-[#3b5bdb]" : "text-[#94a3b8]"}>
      <circle cx="7.5" cy="7.5" r="6" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M7.5 4v3.5l2.5 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
