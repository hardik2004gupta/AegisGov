interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center mb-3 text-red-500">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4"/>
          <path d="M8 5v3.5M8 11h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="text-[13px] font-medium text-[#0f172a] mb-1">
        {message ?? "Unable to load data"}
      </div>
      <div className="text-[12px] text-[#94a3b8]">The backend may be temporarily unavailable.</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-3 py-1.5 text-[12px] bg-white border border-[#e4e7ec] rounded-lg text-[#475569] hover:border-[#cdd2da] hover:text-[#0f172a] transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}
