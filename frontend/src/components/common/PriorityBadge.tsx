import React from 'react';

interface PriorityBadgeProps {
  priority: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  const norm = (priority || '').toUpperCase();

  if (norm === 'HIGH') {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-mono tracking-wider font-semibold text-amber-400">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
        HIGH PRIORITY
      </span>
    );
  }
  if (norm === 'MEDIUM') {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-mono tracking-wider font-semibold text-slate-400">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
        MEDIUM
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-mono tracking-wider font-semibold text-slate-500">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
      LOW
    </span>
  );
};
