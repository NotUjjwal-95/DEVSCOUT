import React from 'react';
import { EvidenceItem } from '../../types/research';
import { SourceBadge } from '../common/SourceBadge';
import { ExternalLink, ShieldCheck, ChevronRight } from 'lucide-react';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  questionText?: string;
  onSelect: (evidence: EvidenceItem) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  questionText,
  onSelect
}) => {
  return (
    <article
      onClick={() => onSelect(evidence)}
      className="group relative bg-[#101522] hover:bg-[#141B2C] border border-slate-800/80 hover:border-slate-700 rounded-lg p-4 transition-all duration-150 cursor-pointer flex flex-col justify-between"
    >
      <div>
        {/* Source and Domain header with zero-pill formatting */}
        <div className="flex items-center justify-between gap-2 text-xs mb-2">
          <div className="flex items-center gap-2">
            <SourceBadge source={evidence.sourceType} />
            <span aria-hidden="true" className="text-slate-600">·</span>
            <span className="font-mono text-slate-400 text-xs truncate max-w-[180px] sm:max-w-[240px]">
              {evidence.domain}
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-mono">
            {evidence.verified && (
              <span className="inline-flex items-center gap-1 text-emerald-400 font-mono text-[11px]">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                VERIFIED
              </span>
            )}
            <span aria-hidden="true" className="text-slate-700">·</span>
            <span className="text-slate-400 font-mono text-[11px]">
              {evidence.relevance}
            </span>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-slate-100 group-hover:text-blue-300 transition-colors leading-snug mb-2 line-clamp-1">
          {evidence.title}
        </h3>

        {/* Snippet */}
        <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 mb-3 font-sans">
          "{evidence.snippet}"
        </p>
      </div>

      {/* Footer info: Related Question & Action */}
      <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs">
        {questionText ? (
          <span className="text-slate-400 truncate max-w-[70%] text-[11px]" title={questionText}>
            Q: {questionText}
          </span>
        ) : (
          <span className="text-slate-400 font-mono text-[11px]">
            {new Date(evidence.timestamp).toLocaleDateString()}
          </span>
        )}

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-blue-400 group-hover:underline inline-flex items-center gap-0.5">
            Inspect
            <ChevronRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (!evidence.url.startsWith('internal://')) {
                window.open(evidence.url, '_blank', 'noopener,noreferrer');
              } else {
                onSelect(evidence);
              }
            }}
            title="Open original resource"
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </article>
  );
};
