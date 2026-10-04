import React, { useState } from 'react';
import { DecisionReport, ResearchSession, EvidenceItem } from '../../types/research';
import { EvidenceDetailModal } from '../evidence/EvidenceDetailModal';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Copy,
  Check,
  Download,
  Share2,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Scale,
  Sparkles,
  Layers,
  Terminal
} from 'lucide-react';

interface DecisionReportViewProps {
  session: ResearchSession;
  onNavigateToEvidence?: () => void;
}

export const DecisionReportView: React.FC<DecisionReportViewProps> = ({
  session,
  onNavigateToEvidence
}) => {
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [copiedMarkdown, setCopiedMarkdown] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'alternatives' | 'tradeoffs' | 'considerations' | 'sources'>('overview');

  const report = session.report;

  if (!report) {
    return (
      <div className="text-center py-20 bg-[#0E131E] border border-slate-800 rounded-lg p-8">
        <Sparkles className="w-10 h-10 text-blue-500 mx-auto mb-3 animate-pulse" />
        <h2 className="text-base font-semibold text-slate-100 mb-2">Decision Report in Synthesis</h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
          The research engine is still collecting and evaluating evidence for this project. Once the 8-stage pipeline completes, the grounded decision report will appear here.
        </p>
        <button
          onClick={onNavigateToEvidence}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-md transition-colors"
        >
          <span>Inspect Active Workspace</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  const findEvidence = (id: string): EvidenceItem | undefined => {
    return session.evidence.find(e => e.id === id);
  };

  const handleOpenEvidence = (id: string) => {
    const item = findEvidence(id);
    if (item) {
      setSelectedEvidence(item);
    }
  };

  const handleCopyMarkdown = () => {
    const md = `# DEVSCOUT DECISION REPORT
Project: ${session.projectName}
Objective: ${session.objective}
Scale: ${session.scale} | Budget: ${session.budget}

## EXECUTIVE SUMMARY
${report.executiveSummary}

## RECOMMENDED APPROACH: ${report.recommendedApproach.title} (Fit: ${report.recommendedApproach.fitLevel})
${report.recommendedApproach.architectureSummary}

### Why It Fits:
${report.recommendedApproach.whyItFits.map(w => `- ${w.point}`).join('\n')}

## ALTERNATIVES CONSIDERED
${report.alternatives.map(a => `### ${a.title} (Fit: ${a.fitLevel})\n${a.summary}\nPros: ${a.pros.join(', ')}\nCons: ${a.cons.join(', ')}\nVerdict: ${a.verdict}`).join('\n\n')}

## TRADE-OFF ANALYSIS
${report.tradeoffs.map(t => `- **${t.dimension}**: ${t.analysis} (Selected: ${t.winner})`).join('\n')}

## TECHNICAL CONSIDERATIONS
${report.technicalConsiderations.map(tc => `### ${tc.category}\n${tc.guidance}\nRule: ${tc.actionableRule}`).join('\n\n')}
`;
    navigator.clipboard.writeText(md);
    setCopiedMarkdown(true);
    setTimeout(() => setCopiedMarkdown(false), 2000);
  };

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(session, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `devscout-report-${session.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6">
      {/* Header and Quick Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1 font-mono">
            <span>ARCHITECTURE DECISION RECORD</span>
            <span aria-hidden="true" className="text-slate-600">·</span>
            <span className="text-emerald-400 font-semibold inline-flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              MULTI-SOURCE GROUNDED
            </span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            {session.projectName}
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            {session.objective}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleCopyMarkdown}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 border border-slate-700/80 rounded-md transition-colors"
          >
            {copiedMarkdown ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedMarkdown ? 'Copied Markdown' : 'Copy Markdown'}</span>
          </button>
          <button
            onClick={handleExportJSON}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 border border-slate-700/80 rounded-md transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800/70 overflow-x-auto pb-1 text-xs">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-3 py-2 font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'overview'
              ? 'text-blue-400 border-blue-500 bg-blue-950/20'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Executive Summary & Recommendation
        </button>
        <button
          onClick={() => setActiveTab('alternatives')}
          className={`px-3 py-2 font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'alternatives'
              ? 'text-blue-400 border-blue-500 bg-blue-950/20'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Alternatives ({report.alternatives.length})
        </button>
        <button
          onClick={() => setActiveTab('tradeoffs')}
          className={`px-3 py-2 font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'tradeoffs'
              ? 'text-blue-400 border-blue-500 bg-blue-950/20'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Trade-off Matrix ({report.tradeoffs.length})
        </button>
        <button
          onClick={() => setActiveTab('considerations')}
          className={`px-3 py-2 font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'considerations'
              ? 'text-blue-400 border-blue-500 bg-blue-950/20'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Technical Considerations ({report.technicalConsiderations.length})
        </button>
        <button
          onClick={() => setActiveTab('sources')}
          className={`px-3 py-2 font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'sources'
              ? 'text-blue-400 border-blue-500 bg-blue-950/20'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Grounding Sources ({session.evidence.length})
        </button>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <section className="bg-[#0F1420] border border-slate-800 rounded-lg p-5">
            <span className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2">
              Executive Summary
            </span>
            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {report.executiveSummary}
            </p>
          </section>

          {/* Recommended Approach Section */}
          <section className="bg-gradient-to-b from-[#11192C] to-[#0E1422] border-2 border-blue-600/40 rounded-lg p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div>
                <span className="text-[11px] font-mono tracking-wider uppercase text-blue-400 font-semibold block mb-1">
                  RECOMMENDED APPROACH
                </span>
                <h2 className="text-lg font-bold text-slate-50 font-mono">
                  {report.recommendedApproach.title}
                </h2>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-center">
                <span className="text-xs font-mono text-slate-400">Architectural Fit:</span>
                <span className="px-2.5 py-1 text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 border border-emerald-700/80 rounded-md">
                  {report.recommendedApproach.fitLevel} FIT
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-sans mb-6 p-3.5 bg-slate-950/60 rounded-md border border-slate-800">
              {report.recommendedApproach.architectureSummary}
            </p>

            {/* Why This Fits (with evidence connections) */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                  Why This Fits Your Technical Criteria
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  Click [Why? / Evidence] for primary source citations
                </span>
              </div>

              <div className="space-y-2.5">
                {report.recommendedApproach.whyItFits.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-[#121827] border border-slate-800/80 hover:border-slate-700 rounded-md transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <p className="text-xs text-slate-200 leading-relaxed font-sans">
                        {item.point}
                      </p>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-center">
                      {item.evidenceIds.map((evId) => {
                        const ev = findEvidence(evId);
                        if (!ev) return null;
                        return (
                          <button
                            key={evId}
                            onClick={() => handleOpenEvidence(evId)}
                            title={`Inspect evidence: ${ev.title}`}
                            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-mono text-blue-300 hover:text-white bg-blue-950/70 hover:bg-blue-900 border border-blue-800/60 rounded transition-colors"
                          >
                            <span className="text-[10px] opacity-75">{ev.sourceType}:</span>
                            <span className="truncate max-w-[80px]">{ev.domain.replace('www.', '')}</span>
                            <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Quick Alternatives preview */}
          <section className="bg-[#0F1420] border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
                Evaluated Alternatives at a Glance
              </span>
              <button
                onClick={() => setActiveTab('alternatives')}
                className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1"
              >
                <span>Full comparison</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {report.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  onClick={() => setActiveTab('alternatives')}
                  className="p-3.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-md transition-colors cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1.5">
                      <span className="text-xs font-semibold font-mono text-slate-200">
                        {alt.title}
                      </span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        alt.fitLevel.toUpperCase() === 'HIGH' ? 'text-emerald-400 bg-emerald-950/60' :
                        alt.fitLevel.toUpperCase() === 'MEDIUM' ? 'text-amber-400 bg-amber-950/60' : 'text-slate-400 bg-slate-800'
                      }`}>
                        {alt.fitLevel.toUpperCase()} FIT
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed font-sans mb-2">
                      {alt.summary}
                    </p>
                  </div>
                  <span className="text-[11px] text-slate-400 italic">
                    "{alt.verdict}"
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {/* Alternatives Tab */}
      {activeTab === 'alternatives' && (
        <div className="space-y-4">
          <div className="text-xs text-slate-400 mb-2">
            Detailed comparison of architecture candidates investigated during the research spike.
          </div>
          {report.alternatives.map((alt, idx) => (
            <div key={idx} className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-3">
                  <h3 className="text-base font-semibold text-slate-100 font-mono">
                    {alt.title}
                  </h3>
                  <span className={`text-xs font-mono px-2 py-0.5 rounded font-medium ${
                    alt.fitLevel.toUpperCase() === 'HIGH' ? 'text-emerald-300 bg-emerald-950/80 border border-emerald-800' :
                    alt.fitLevel.toUpperCase() === 'MEDIUM' ? 'text-amber-300 bg-amber-950/80 border border-amber-800' :
                    'text-slate-400 bg-slate-800/80 border border-slate-700'
                  }`}>
                    {alt.fitLevel.toUpperCase()} FIT
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  {alt.evidenceIds.map(evId => (
                    <button
                      key={evId}
                      onClick={() => handleOpenEvidence(evId)}
                      className="px-2 py-1 text-[11px] font-mono text-blue-400 hover:text-white bg-blue-950/60 hover:bg-blue-900 border border-blue-900/60 rounded transition-colors inline-flex items-center gap-1"
                    >
                      <span>Evidence {evId}</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  ))}
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {alt.summary}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                <div className="p-3 bg-emerald-950/15 border border-emerald-900/30 rounded-md">
                  <span className="block text-[11px] font-mono uppercase tracking-wider text-emerald-400 mb-2 font-semibold">
                    Advantages & Strengths
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-300 font-sans">
                    {alt.pros.map((p, pIdx) => (
                      <li key={pIdx} className="flex items-start gap-2">
                        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-3 bg-amber-950/15 border border-amber-900/30 rounded-md">
                  <span className="block text-[11px] font-mono uppercase tracking-wider text-amber-400 mb-2 font-semibold">
                    Trade-offs & Constraints
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-300 font-sans">
                    {alt.cons.map((c, cIdx) => (
                      <li key={cIdx} className="flex items-start gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="p-3 bg-slate-900/70 border border-slate-800 rounded-md text-xs">
                <span className="font-mono text-slate-400 text-[11px] mr-2">VERDICT:</span>
                <span className="text-slate-200 font-medium font-sans">{alt.verdict}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Trade-offs Tab */}
      {activeTab === 'tradeoffs' && (
        <div className="space-y-4">
          <div className="text-xs text-slate-400 mb-2">
            Engineering trade-offs identified and resolved by evidence comparison.
          </div>
          {report.tradeoffs.map((item, idx) => (
            <div key={idx} className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Scale className="w-4 h-4 text-blue-400" />
                  <h3 className="text-sm font-semibold text-slate-100 font-mono">
                    {item.dimension}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">Decided Direction:</span>
                  <span className="text-xs font-mono font-bold text-blue-300 bg-blue-950/80 px-2 py-0.5 border border-blue-800 rounded">
                    {item.winner}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {item.analysis}
              </p>

              <div className="flex items-center gap-2 pt-2 text-xs font-mono text-slate-400">
                <span>Supporting evidence:</span>
                {item.evidenceIds.map(evId => (
                  <button
                    key={evId}
                    onClick={() => handleOpenEvidence(evId)}
                    className="text-blue-400 hover:underline hover:text-blue-300"
                  >
                    #{evId}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Technical Considerations Tab */}
      {activeTab === 'considerations' && (
        <div className="space-y-4">
          <div className="text-xs text-slate-400 mb-2">
            Operational rules, gotchas, and production invariants for the engineering team.
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.technicalConsiderations.map((tc, idx) => (
              <div key={idx} className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Terminal className="w-4 h-4 text-blue-400" />
                    <h3 className="text-sm font-semibold font-mono text-slate-100">
                      {tc.category}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans mb-4">
                    {tc.guidance}
                  </p>
                </div>

                <div className="p-3 bg-slate-950/80 border-l-2 border-blue-500 rounded-r-md text-xs font-mono text-blue-200">
                  <span className="text-[10px] text-slate-400 block mb-0.5 uppercase tracking-wider font-sans">
                    Actionable Implementation Rule
                  </span>
                  {tc.actionableRule}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources Tab */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              All {session.evidence.length} validated source documents backing this report.
            </span>
            <button
              onClick={onNavigateToEvidence}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1"
            >
              <span>Open in Evidence Explorer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {session.evidence.map((ev) => (
              <div
                key={ev.id}
                onClick={() => setSelectedEvidence(ev)}
                className="p-3.5 bg-[#0F1420] hover:bg-[#131929] border border-slate-800 hover:border-slate-700 rounded-lg cursor-pointer transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                    <span className="text-blue-400 font-semibold">{ev.sourceType}</span>
                    <span className="text-slate-400">{ev.domain}</span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200 mb-1.5 line-clamp-1">
                    {ev.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    "{ev.snippet}"
                  </p>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-400 mt-2 font-mono">
                  <span>Relevance: {ev.relevance}</span>
                  <span className="text-blue-400 hover:underline">Inspect excerpt &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Modal */}
      {selectedEvidence && (
        <EvidenceDetailModal
          evidence={selectedEvidence}
          questionText={(session.plan?.questions || session.questions || []).find(q => q.id === selectedEvidence.relatedQuestionId)?.question}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
};
