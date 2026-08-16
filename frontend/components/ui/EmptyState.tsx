interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {icon && (
        <div className="w-12 h-12 rounded-xl bg-[#f7f8fa] border border-[#e4e7ec] flex items-center justify-center mb-4 text-[#94a3b8]">
          {icon}
        </div>
      )}
      <div className="text-[14px] font-medium text-[#0f172a] mb-1">{title}</div>
      {description && (
        <div className="text-[13px] text-[#94a3b8] max-w-xs leading-relaxed">{description}</div>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
