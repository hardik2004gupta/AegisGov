"use client";

import { useEffect } from "react";

interface ToastProps {
  message: string;
  type: "success" | "error" | "info";
  onClose: () => void;
}

export function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [onClose]);

  const colors = {
    success: "bg-emerald-50 border-emerald-300 text-emerald-800",
    error: "bg-red-50 border-red-300 text-red-800",
    info: "bg-blue-50 border-blue-300 text-blue-800",
  };

  const icons = { success: "✓", error: "✗", info: "ℹ" };

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg text-sm font-medium ${colors[type]}`}
    >
      <span className="font-bold">{icons[type]}</span>
      {message}
      <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100">
        ×
      </button>
    </div>
  );
}
