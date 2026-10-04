import React, { useState } from 'react';
import { EvidenceItem } from '../../types/research';
import { SourceBadge } from '../common/SourceBadge';
import { ExternalLink, Check, Copy, X, ShieldCheck } from 'lucide-react';

interface EvidenceDetailModalProps {
  evidence: EvidenceItem | null;
  onClose: () => void;
  questionText?: string;
}

export const EvidenceDetailModal: React.FC<EvidenceDetailModalProps> = ({
  evidence,
  onClose,
  questionText
}) => {
  const [copied, setCopied] = useState(false);

  if (!evidence) return null;

  const handleCopy = () => {
    const text = `"${evidence.fullQuote || evidence.snippet}" — ${evidence.title} (${evidence.url})`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#111622] border border-slate-800 rounded-lg shadow-2xl p-6 overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <SourceBadge source={evidence.sourceType} />
              <span aria-hidden="true" className="text-slate-600">·</span>
              <span className="font-mono text-slate-400">{evidence.domain}</span>
              {evidence.verified && (
                <>
                  <span aria-hidden="true" className="text-slate-600">·</span>
                  <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px] font-mono">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    VERIFIED EVIDENCE
                  </span>
                </>
              )}
            </div>
            <h2 id="evidence-modal-title" className="text-base font-semibold text-slate-100 leading-snug">
              {evidence.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="py-4 space-y-4 overflow-y-auto">
          {questionText && (
            <div className="p-3 bg-slate-900/80 border border-slate-800/70 rounded-md">
              <span className="block text-[11px] uppercase tracking-wider font-mono text-slate-400 mb-1">
                Answering Architectural Question
              </span>
              <p className="text-xs text-slate-300 font-medium">
                {questionText}
              </p>
            </div>
          )}

          <div>
            <span className="block text-[11px] uppercase tracking-wider font-mono text-slate-400 mb-2">
              Extracted Evidence Quote
            </span>
            <blockquote className="p-4 bg-slate-950/70 border-l-2 border-blue-500 rounded-r-md text-sm text-slate-200 leading-relaxed font-sans">
              "{evidence.fullQuote || evidence.snippet}"
            </blockquote>
          </div>

          {evidence.metadata && Object.keys(evidence.metadata).length > 0 && (
            <div>
              <span className="block text-[11px] uppercase tracking-wider font-mono text-slate-400 mb-2">
                Technical Metadata
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-3 bg-slate-900/50 border border-slate-800/60 rounded-md">
                {Object.entries(evidence.metadata).map(([key, value]) => (
                  <div key={key} className="text-xs">
                    <span className="text-slate-400 block capitalize font-mono text-[10px]">
                      {key.replace(/([A-Z])/g, ' $1')}
                    </span>
                    <span className="font-mono text-slate-200">
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60 font-mono">
            <span>Relevance: <strong className="text-slate-300 font-semibold">{evidence.relevance}</strong></span>
            <span>Recorded: {new Date(evidence.timestamp).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-md transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Citation Copied' : 'Copy Citation'}</span>
          </button>

          <a
            href={evidence.url.startsWith('internal://') ? '#' : evidence.url}
            target={evidence.url.startsWith('internal://') ? undefined : '_blank'}
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-blue-100 bg-blue-600 hover:bg-blue-500 rounded-md transition-colors"
          >
            <span>Open Source</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
};
