import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisGov",
  description:
    "Secure Runtime Governance & Zero-Trust Execution Gateway for Agentic AI",
};

const navLinks = [
  { href: "/", label: "Agent Console" },
  { href: "/approvals", label: "Approvals" },
  { href: "/audit", label: "Audit Explorer" },
  { href: "/runtime", label: "Runtime Dashboard" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-aegis-950 text-slate-100 font-mono">
        {/* ── Header ── */}
        <header className="border-b border-slate-800 bg-aegis-900/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-aegis-500 font-bold text-xl tracking-tight">
                AEGISGOV
              </span>
              <span className="text-slate-500 text-xs uppercase tracking-widest">
                Zero-Trust Agent Gateway
              </span>
            </div>
            <nav className="flex items-center gap-1">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="px-3 py-1.5 rounded text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </header>

        {/* ── Main content ── */}
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>

        {/* ── Footer ── */}
        <footer className="border-t border-slate-800 mt-auto">
          <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between text-xs text-slate-600">
            <span>AegisGov v0.1.0 — Phase 1: Foundation</span>
            <span>Agents propose actions. AegisGov owns execution authority.</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
