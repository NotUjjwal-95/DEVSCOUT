import React, { useState } from 'react';
import { ResearchSession, ResearchStage, ResearchQuestion, EvidenceItem } from '../../types/research';
import { SourceBadge } from '../common/SourceBadge';
import { PriorityBadge } from '../common/PriorityBadge';
import { EvidenceDetailModal } from '../evidence/EvidenceDetailModal';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Sparkles,
  ArrowRight,
  Terminal,
  FastForward,
  StopCircle,
  HelpCircle,
  Cpu,
  Layers
} from 'lucide-react';

interface WorkspaceViewProps {
  session: ResearchSession;
  onFastForward: () => void;
  onCancel: () => void;
  onNavigateToReport: () => void;
  onNavigateToEvidence: () => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  session,
  onFastForward,
  onCancel,
  onNavigateToReport,
  onNavigateToEvidence
}) => {
  const questions = session.plan?.questions || session.questions || [];
  const events = session.events || session.activityEvents || [];
  const technologies = session.technologies || session.requirementAnalysis?.technologies || [];
  const scale = session.scale || session.requirementAnalysis?.targetScale || 'Standard';
  const budget = session.budget || session.requirementAnalysis?.budgetTier || 'Standard';

  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(
    questions[0]?.id || null
  );
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);

  const toggleQuestion = (id: string) => {
    setExpandedQuestionId(prev => (prev === id ? null : id));
  };

  const getStageIcon = (stage: ResearchStage) => {
    if (stage.status === 'completed') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
    }
    if (stage.status === 'running') {
      return <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />;
    }
    if (stage.status === 'failed') {
      return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
    }
    return <Clock className="w-4 h-4 text-slate-600 shrink-0" />;
  };

  const getStageStatusText = (stage: ResearchStage) => {
    if (stage.status === 'completed') return 'COMPLETED';
    if (stage.status === 'running') return 'RUNNING';
    if (stage.status === 'failed') return 'FAILED';
    return 'QUEUED';
  };

  const completedStagesCount = session.stages.filter(s => s.status === 'completed').length;
  const isRunning = session.state === 'planning' || session.state === 'researching' || session.state === 'processing';

  const getStateBadgeText = () => {
    const st = session.state || 'idle';
    switch (st) {
      case 'planning': return 'PIPELINE PLANNING';
      case 'researching': return 'MULTI-SOURCE RESEARCHING';
      case 'processing': return 'EVIDENCE PROCESSING';
      case 'completed': return 'INVESTIGATION COMPLETED';
      case 'failed': return 'PIPELINE HALTED';
      default: return 'ENGINE IDLE';
    }
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono mb-1">
            <span>RESEARCH WORKSPACE</span>
            <span aria-hidden="true" className="text-slate-600">·</span>
            <span className={isRunning ? 'text-blue-400 font-semibold flex items-center gap-1.5' : 'text-emerald-400 font-semibold flex items-center gap-1.5'}>
              {isRunning && <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />}
              {getStateBadgeText()}
            </span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            {session.projectName}
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl line-clamp-2">
            {session.objective}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {isRunning ? (
            <>
              <button
                onClick={onFastForward}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-blue-200 bg-blue-600/30 hover:bg-blue-600/50 border border-blue-500/50 rounded-md transition-colors"
                title="Fast forward simulated stages to final report"
              >
                <FastForward className="w-3.5 h-3.5 text-blue-300" />
                <span>Fast Forward Engine</span>
              </button>
              <button
                onClick={onCancel}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-rose-300 hover:text-white bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/60 rounded-md transition-colors"
              >
                <StopCircle className="w-3.5 h-3.5" />
                <span>Halt</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onNavigateToEvidence}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 border border-slate-700/80 rounded-md transition-colors"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Evidence ({session.evidence.length})</span>
              </button>
              <button
                onClick={onNavigateToReport}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-md shadow-xs transition-colors"
              >
                <span>View Decision Report</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Grid: Pipeline stages + Central activity feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 8-Stage Research Pipeline (5 cols on lg) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-blue-400" />
              Research Pipeline
            </h2>
            <span className="text-[11px] font-mono text-slate-400 tabular-nums">
              {completedStagesCount} / {session.stages.length} Stages
            </span>
          </div>

          <div className="space-y-2 bg-[#0F1420] border border-slate-800/90 rounded-lg p-3">
            {session.stages.map((stage, idx) => {
              const isActive = stage.status === 'running';
              const isDone = stage.status === 'completed';

              return (
                <div
                  key={stage.id}
                  className={`p-2.5 rounded-md border transition-colors flex items-start justify-between gap-3 ${
                    isActive
                      ? 'bg-blue-950/30 border-blue-600/60 shadow-xs'
                      : isDone
                      ? 'bg-slate-900/40 border-slate-800/60'
                      : 'bg-slate-950/20 border-slate-800/30 opacity-60'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5">{getStageIcon(stage)}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-200">
                          {idx + 1}. {stage.name}
                        </span>
                        {isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 leading-tight mt-0.5 font-sans">
                        {stage.description}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`text-[10px] font-mono block ${
                        isActive
                          ? 'text-blue-400 font-bold'
                          : isDone
                          ? 'text-emerald-400'
                          : 'text-slate-400'
                      }`}
                    >
                      {getStageStatusText(stage)}
                    </span>
                    {stage.durationSeconds && (
                      <span className="text-[10px] text-slate-400 font-mono tabular-nums block">
                        {stage.durationSeconds}s
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Context Summary Box */}
          <div className="bg-[#0F1420] border border-slate-800/90 rounded-lg p-4 space-y-2 text-xs">
            <span className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-1">
              Active Parameters
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <span className="text-slate-400 block text-[10px]">SCALE:</span>
                <span className="text-slate-300 truncate block">{scale}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">BUDGET:</span>
                <span className="text-slate-300 truncate block">{budget}</span>
              </div>
            </div>
            {technologies.length > 0 && (
              <div className="pt-2 border-t border-slate-800 text-xs">
                <span className="text-slate-400 block text-[10px] font-mono mb-1">TECH STACK:</span>
                <div className="flex flex-wrap gap-1 text-[11px] text-slate-300 font-mono">
                  {technologies.map(t => (
                    <span key={t} className="px-1.5 py-0.5 bg-slate-900 border border-slate-700/60 rounded text-[10px]">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Activity Feed (7 cols on lg) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-blue-400" />
              Activity Feed
            </h2>
            <span className="text-[11px] font-mono text-slate-400 tabular-nums">
              {events.length} events logged
            </span>
          </div>

          {/* Activity feed console style */}
          <div className="bg-[#0A0E17] border border-slate-800 rounded-lg p-4 font-mono text-xs max-h-[380px] overflow-y-auto space-y-2.5">
            {events.length === 0 ? (
              <div className="text-slate-400 text-center py-10 font-sans text-xs">
                Initializing research engine activity log...
              </div>
            ) : (
              events.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-2.5 text-xs border-b border-slate-900 pb-2 last:border-b-0 last:pb-0"
                >
                  <span className="text-slate-400 shrink-0 text-[11px] tabular-nums">
                    [{event.timestamp}]
                  </span>
                  <span
                    className={`font-semibold shrink-0 uppercase text-[10px] px-1 py-0.5 rounded ${
                      event.type === 'success'
                        ? 'text-emerald-400 bg-emerald-950/60'
                        : event.type === 'artifact'
                        ? 'text-cyan-400 bg-cyan-950/60'
                        : event.type === 'warning'
                        ? 'text-amber-400 bg-amber-950/60'
                        : 'text-blue-400 bg-blue-950/60'
                    }`}
                  >
                    {event.stageId}
                  </span>
                  <span className="text-slate-200 font-sans text-xs leading-relaxed">
                    {event.message}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Research Questions Section */}
      <div className="space-y-4 pt-4 border-t border-slate-800/80">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Research Planner Questions
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded architectural hypotheses driving task dispatch and multi-source evidence retrieval.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {questions.length} questions formulated
          </span>
        </div>

        <div className="space-y-3">
          {questions.map((q) => {
            const isExpanded = expandedQuestionId === q.id;

            return (
              <div
                key={q.id}
                className="bg-[#0F1420] border border-slate-800 rounded-lg overflow-hidden transition-colors"
              >
                {/* Question Header Accordion Toggle */}
                <div
                  onClick={() => toggleQuestion(q.id)}
                  className="p-4 cursor-pointer hover:bg-slate-900/60 transition-colors flex items-start justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <PriorityBadge priority={q.priority} />
                      <span aria-hidden="true" className="text-slate-600">·</span>
                      <div className="flex items-center gap-1.5">
                        {q.sources.map(src => (
                          <SourceBadge key={src} source={src} size="sm" />
                        ))}
                      </div>
                    </div>

                    <h3 className="text-sm font-semibold text-slate-100 leading-snug">
                      {q.question}
                    </h3>

                    <p className="text-xs text-slate-400 leading-relaxed font-sans">
                      <strong className="text-slate-300 font-semibold font-mono text-[11px]">Why: </strong>
                      {q.why}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 pt-1">
                    <span className="text-[11px] font-mono text-slate-400">
                      {q.tasks.length} tasks · {q.evidenceIds.length} sources
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Tasks & Evidence */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 border-t border-slate-800/80 bg-slate-950/40 space-y-3">
                    {/* Tasks list */}
                    <div>
                      <span className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                        Associated Source Tasks
                      </span>
                      <div className="space-y-1.5">
                        {q.tasks.map((task) => (
                          <div
                            key={task.id}
                            className="flex items-center justify-between text-xs p-2 bg-slate-900/70 border border-slate-800/70 rounded-md font-sans"
                          >
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                              <span className="text-slate-200">{task.description}</span>
                            </div>
                            <div className="flex items-center gap-2 font-mono text-[11px]">
                              {task.query && (
                                <span className="text-slate-400 hidden md:inline truncate max-w-xs">
                                  "{task.query}"
                                </span>
                              )}
                              <SourceBadge source={task.sourceType || task.source || 'web'} size="sm" showIcon={false} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Linked Evidence items */}
                    {q.evidenceIds.length > 0 && (
                      <div>
                        <span className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                          Extracted Evidence ({q.evidenceIds.length})
                        </span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {q.evidenceIds.map((evId) => {
                            const ev = session.evidence.find(e => e.id === evId);
                            if (!ev) return null;

                            return (
                              <div
                                key={evId}
                                onClick={() => setSelectedEvidence(ev)}
                                className="p-2.5 bg-slate-900/90 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 rounded-md cursor-pointer transition-colors"
                              >
                                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                                  <SourceBadge source={ev.sourceType} size="sm" />
                                  <span className="font-mono text-slate-400 truncate max-w-[120px]">{ev.domain}</span>
                                </div>
                                <h4 className="text-xs font-semibold text-slate-200 truncate">
                                  {ev.title}
                                </h4>
                                <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                                  "{ev.snippet}"
                                </p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Evidence detail modal if clicked */}
      {selectedEvidence && (
        <EvidenceDetailModal
          evidence={selectedEvidence}
          questionText={questions.find(q => q.id === selectedEvidence.relatedQuestionId)?.question}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
};
