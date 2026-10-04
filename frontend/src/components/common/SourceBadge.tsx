import React from 'react';
import { SourceType } from '../../types/research';
import { Globe, GitFork, BookOpen } from 'lucide-react';

interface SourceBadgeProps {
  source: SourceType;
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, showIcon = true, size = 'sm' }) => {
  const isSm = size === 'sm';
  const normalized = (source || '').toLowerCase();
  
  if (normalized === 'web') {
    return (
      <span className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-semibold text-blue-400 ${isSm ? 'text-[11px]' : 'text-xs'}`}>
        {showIcon && <Globe className={isSm ? 'w-3 h-3 text-blue-400' : 'w-3.5 h-3.5 text-blue-400'} />}
        <span>WEB</span>
      </span>
    );
  }

  if (normalized === 'github') {
    return (
      <span className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-semibold text-emerald-400 ${isSm ? 'text-[11px]' : 'text-xs'}`}>
        {showIcon && <GitFork className={isSm ? 'w-3 h-3 text-emerald-400' : 'w-3.5 h-3.5 text-emerald-400'} />}
        <span>GITHUB</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-semibold text-cyan-400 ${isSm ? 'text-[11px]' : 'text-xs'}`}>
      {showIcon && <BookOpen className={isSm ? 'w-3 h-3 text-cyan-400' : 'w-3.5 h-3.5 text-cyan-400'} />}
      <span>RAG</span>
    </span>
  );
};
