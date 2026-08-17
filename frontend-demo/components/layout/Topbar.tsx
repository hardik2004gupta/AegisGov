interface TopbarProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

export function Topbar({ title, subtitle, children }: TopbarProps) {
  return (
    <div className="sticky top-0 z-10 border-b border-slate-200 bg-white">
      <div className="bg-amber-50 border-b border-amber-200 px-6 py-1 flex items-center gap-2">
        <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
          Simulated Environment
        </span>
        <span className="text-xs text-amber-600">
          — No backend running. All data is local mock data.
        </span>
      </div>
      <div className="flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {children && <div className="flex items-center gap-3">{children}</div>}
      </div>
    </div>
  );
}
