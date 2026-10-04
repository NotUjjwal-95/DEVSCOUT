import React, { useState } from 'react';
import { ResearchSession } from '../../types/research';
import {
  Clock,
  Search,
  ArrowRight,
  GitFork,
  BookOpen,
  Trash2,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderOpen
} from 'lucide-react';

interface ResearchHistoryViewProps {
  sessions: ResearchSession[];
  onOpenSession: (sessionId: string, targetView: 'workspace' | 'report' | 'evidence') => void;
  onDeleteSession: (sessionId: string) => void;
  onStartNew: () => void;
}

export const ResearchHistoryView: React.FC<ResearchHistoryViewProps> = ({
  sessions,
  onOpenSession,
  onDeleteSession,
  onStartNew
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    const techs = s.technologies || s.requirementAnalysis?.technologies || [];
    return (
      s.projectName.toLowerCase().includes(q) ||
      s.objective.toLowerCase().includes(q) ||
      techs.some(t => t.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            Research History
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Archived architectural investigations, evidence logs, and grounded decision records.
          </p>
        </div>

        <button
          onClick={onStartNew}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-md transition-colors shrink-0"
        >
          <span>+ New Research</span>
        </button>
      </div>

      {/* Search Filter */}
      <div className="flex items-center gap-3 bg-[#0D121D] p-3 rounded-lg border border-slate-800/70">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search past research by project, objective, or tech..."
            className="w-full bg-[#121824] border border-slate-700/80 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-hidden focus:border-blue-500"
          />
        </div>
        <span className="text-xs font-mono text-slate-400 shrink-0">
          {filteredSessions.length} sessions
        </span>
      </div>

      {/* Sessions List */}
      {filteredSessions.length > 0 ? (
        <div className="space-y-3">
          {filteredSessions.map((session) => {
            const isCompleted = session.state === 'completed';
            const isRunning = session.state === 'planning' || session.state === 'researching' || session.state === 'processing';
            const stateLabel = (session.state || 'idle').toUpperCase();
            const repoCount = (session.repositories || session.githubRepos || []).length;
            const scaleDisplay = session.scale || session.requirementAnalysis?.targetScale || 'Standard';

            return (
              <article
                key={session.id}
                className="bg-[#0F1420] hover:bg-[#121827] border border-slate-800 hover:border-slate-700 rounded-lg p-5 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="font-mono text-slate-400">
                      {new Date(session.createdAt).toLocaleDateString()}
                    </span>
                    <span aria-hidden="true" className="text-slate-700">·</span>
                    <span
                      className={`inline-flex items-center gap-1 font-mono text-[11px] font-semibold ${
                        isCompleted
                          ? 'text-emerald-400'
                          : isRunning
                          ? 'text-blue-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {isCompleted && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                      {isRunning && <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />}
                      {!isCompleted && !isRunning && <AlertCircle className="w-3 h-3 text-rose-400" />}
                      {stateLabel}
                    </span>
                  </div>

                  <h3 className="text-base font-semibold text-slate-100 truncate">
                    {session.projectName}
                  </h3>

                  <p className="text-xs text-slate-300 line-clamp-2 font-sans">
                    {session.objective}
                  </p>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono pt-1">
                    <span className="inline-flex items-center gap-1 text-slate-300">
                      <BookOpen className="w-3 h-3 text-blue-400" />
                      {session.evidence.length} Sources
                    </span>
                    <span aria-hidden="true" className="text-slate-700">·</span>
                    <span className="inline-flex items-center gap-1 text-slate-300">
                      <GitFork className="w-3 h-3 text-emerald-400" />
                      {repoCount} Repositories
                    </span>
                    <span aria-hidden="true" className="text-slate-700">·</span>
                    <span className="text-slate-400">
                      Scale: {scaleDisplay}
                    </span>
                  </div>
                </div>

                {/* Right Action buttons */}
                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  <button
                    onClick={() => onDeleteSession(session.id)}
                    title="Delete session"
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => onOpenSession(session.id, 'workspace')}
                    className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 border border-slate-700 rounded-md transition-colors inline-flex items-center gap-1"
                  >
                    <span>Workspace</span>
                  </button>

                  <button
                    onClick={() => onOpenSession(session.id, 'report')}
                    className="px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-md transition-colors inline-flex items-center gap-1"
                  >
                    <span>Open Report</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#0E131E] border border-slate-800 rounded-lg p-6">
          <FolderOpen className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-300 mb-1">No research sessions match</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            Try a different search term or start a fresh technical research investigation.
          </p>
          <button
            onClick={onStartNew}
            className="px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-md"
          >
            Start New Research
          </button>
        </div>
      )}
    </div>
  );
};
