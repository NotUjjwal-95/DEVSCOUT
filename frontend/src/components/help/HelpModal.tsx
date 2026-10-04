import React from 'react';
import { X, ShieldCheck, Compass, GitFork, BookOpen, Globe, Cpu } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#111622] border border-slate-800 rounded-lg shadow-2xl p-6 overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-mono text-blue-400">
              <Compass className="w-4 h-4 text-blue-400" />
              <span>DEVSCOUT ARCHITECTURE ENGINE</span>
            </div>
            <h2 id="help-modal-title" className="text-base font-semibold text-slate-100">
              Technical Research & Grounding Methodology
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-4 overflow-y-auto text-xs text-slate-300 font-sans leading-relaxed">
          <div className="p-3.5 bg-blue-950/20 border border-blue-900/40 rounded-md">
            <h3 className="font-semibold text-blue-300 text-sm mb-1 font-mono">
              Not a Chatbot. A Technical Spike Assistant.
            </h3>
            <p className="text-slate-300 text-xs">
              DEVSCOUT investigates software development and systems engineering problems. Rather than producing hallucinated conversational answers, it runs an 8-stage verification pipeline that extracts evidence directly from official web documentation, active GitHub repositories, and curated distributed systems knowledge bases.
            </p>
          </div>

          <div>
            <h4 className="font-mono text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2">
              The 8-Stage Research Pipeline
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">1. Requirement Analysis</span>
                <span className="text-slate-400 font-sans">Extracts hard constraints, SLA bounds, and scale goals.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">2. Research Planning</span>
                <span className="text-slate-400 font-sans">Formulates architectural hypotheses & priority questions.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">3. Task Generation</span>
                <span className="text-slate-400 font-sans">Dispatches targeted source probes across Web, GitHub, and RAG.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">4. Web Standards Probe</span>
                <span className="text-slate-400 font-sans">Crawls RFC specifications, official guides, and peer benchmarks.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">5. GitHub Repository Audit</span>
                <span className="text-slate-400 font-sans">Audits maintenance cadences, open issues, and code patterns.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">6. Curated RAG Knowledge</span>
                <span className="text-slate-400 font-sans">Queries peer-reviewed trade-off databases for common traps.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">7. Evidence Processing</span>
                <span className="text-slate-400 font-sans">Normalizes claims, ranks source confidence, and deduplicates.</span>
              </div>
              <div className="p-2 bg-slate-900/60 border border-slate-800 rounded">
                <span className="text-blue-400 block font-bold">8. Decision Analysis</span>
                <span className="text-slate-400 font-sans">Generates grounded trade-off matrix & architecture record.</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-mono text-slate-200 text-xs font-semibold uppercase tracking-wider mb-1">
              Evidence Triangulation Guarantee
            </h4>
            <p className="text-slate-400 text-xs">
              Every major recommendation in a DEVSCOUT report includes visual citations to backing evidence items. Click any <strong className="text-blue-400">[Why?]</strong> or evidence badge in the report to inspect the exact quote, domain, and timestamp.
            </p>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-md"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
