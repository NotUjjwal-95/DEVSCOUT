import React, { useState, useMemo } from 'react';
import { ResearchSession, EvidenceSourceType, Evidence } from '../../types';
import { EvidenceCard } from './EvidenceCard';
import { GithubRepoCard } from './GithubRepoCard';
import { EvidenceDetailModal } from './EvidenceDetailModal';
import { Search, SlidersHorizontal, GitFork, BookOpen, Globe, LayoutGrid, Layers } from 'lucide-react';

interface EvidenceExplorerViewProps {
  session: ResearchSession;
}

type FilterSource = 'all' | EvidenceSourceType;
type SortOption = 'relevance' | 'newest' | 'domain';
type ViewMode = 'all-evidence' | 'repos-only';

export const EvidenceExplorerView: React.FC<EvidenceExplorerViewProps> = ({ session }) => {
  const [activeFilter, setActiveFilter] = useState<FilterSource>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>('relevance');
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('all-evidence');

  const repos = session.repositories || session.githubRepos || [];
  const questions = session.plan?.questions || session.questions || [];

  // Counts
  const counts = useMemo(() => {
    const web = session.evidence.filter(e => e.sourceType.toLowerCase() === 'web').length;
    const github = session.evidence.filter(e => e.sourceType.toLowerCase() === 'github').length;
    const rag = session.evidence.filter(e => e.sourceType.toLowerCase() === 'rag').length;
    return {
      all: session.evidence.length,
      web,
      github,
      rag,
      repos: repos.length
    };
  }, [session.evidence, repos]);

  // Filtered and sorted evidence
  const filteredEvidence = useMemo(() => {
    let items = [...session.evidence];

    if (activeFilter !== 'all') {
      items = items.filter(e => e.sourceType.toLowerCase() === activeFilter.toLowerCase());
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      items = items.filter(
        e =>
          e.title.toLowerCase().includes(q) ||
          e.snippet.toLowerCase().includes(q) ||
          e.domain.toLowerCase().includes(q)
      );
    }

    if (sortOption === 'relevance') {
      const order: Record<string, number> = { primary: 4, benchmark: 3, high: 2, medium: 1 };
      items.sort((a, b) => (order[b.relevance.toLowerCase()] || 0) - (order[a.relevance.toLowerCase()] || 0));
    } else if (sortOption === 'newest') {
      items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } else if (sortOption === 'domain') {
      items.sort((a, b) => a.domain.localeCompare(b.domain));
    }

    return items;
  }, [session.evidence, activeFilter, searchQuery, sortOption]);

  const filteredRepos = useMemo(() => {
    if (!searchQuery.trim()) return repos;
    const q = searchQuery.toLowerCase().trim();
    return repos.filter(
      r =>
        (r.name || r.repo).toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.language.toLowerCase().includes(q)
    );
  }, [repos, searchQuery]);

  const getQuestionText = (questionId: string) => {
    return questions.find(q => q.id === questionId)?.question;
  };

  return (
    <div className="space-y-6">
      {/* Top Bar / View Title & Mode Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            Evidence Explorer
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Audited multi-source technical groundings across web standards, active repositories, and internal knowledge bases.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 p-1 bg-slate-900 border border-slate-800 rounded-lg shrink-0">
          <button
            onClick={() => setViewMode('all-evidence')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              viewMode === 'all-evidence'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>All Evidence ({counts.all})</span>
          </button>
          <button
            onClick={() => setViewMode('repos-only')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              viewMode === 'repos-only'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>Repositories ({counts.repos})</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#0D121D] p-3 rounded-lg border border-slate-800/70">
        {/* Source Filter Segmented Buttons */}
        {viewMode === 'all-evidence' ? (
          <div className="flex flex-wrap items-center gap-1">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeFilter === 'all'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Sources ({counts.all})
            </button>
            <button
              onClick={() => setActiveFilter('web')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeFilter === 'web'
                  ? 'bg-blue-950/80 text-blue-300 border border-blue-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Globe className="w-3.5 h-3.5 text-blue-400" />
              <span>Web ({counts.web})</span>
            </button>
            <button
              onClick={() => setActiveFilter('github')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeFilter === 'github'
                  ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitFork className="w-3.5 h-3.5 text-emerald-400" />
              <span>GitHub ({counts.github})</span>
            </button>
            <button
              onClick={() => setActiveFilter('rag')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeFilter === 'rag'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span>RAG Knowledge ({counts.rag})</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-300 font-mono">
            <GitFork className="w-4 h-4 text-emerald-400" />
            <span>Target Repositories ({repos.length} inspected)</span>
          </div>
        )}

        {/* Search & Sort */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={viewMode === 'all-evidence' ? "Filter snippets, domains..." : "Search repositories..."}
              className="w-full bg-[#121824] border border-slate-700/80 rounded-md pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-hidden focus:border-blue-500"
            />
          </div>

          {viewMode === 'all-evidence' && (
            <div className="flex items-center gap-1.5 shrink-0">
              <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value as SortOption)}
                aria-label="Sort evidence items"
                className="bg-[#121824] border border-slate-700/80 rounded-md px-2 py-1.5 text-xs text-slate-300 focus:outline-hidden focus:border-blue-500"
              >
                <option value="relevance">Most relevant</option>
                <option value="newest">Newest</option>
                <option value="domain">Domain / Source</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Grid Content */}
      {viewMode === 'all-evidence' ? (
        filteredEvidence.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredEvidence.map((evidence) => (
              <EvidenceCard
                key={evidence.id}
                evidence={evidence}
                questionText={getQuestionText(evidence.relatedQuestionId)}
                onSelect={(ev) => setSelectedEvidence(ev)}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[#0E131E] border border-slate-800 rounded-lg p-6">
            <LayoutGrid className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-300 mb-1">No evidence items match filter</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Try adjusting your search query or reset the source filter to view all collected findings.
            </p>
          </div>
        )
      ) : (
        filteredRepos.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRepos.map((repo) => (
              <GithubRepoCard key={repo.id} repo={repo} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[#0E131E] border border-slate-800 rounded-lg p-6">
            <GitFork className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-300 mb-1">No repositories found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No audited GitHub repositories matched your search query.
            </p>
          </div>
        )
      )}

      {/* Evidence Detail Modal */}
      {selectedEvidence && (
        <EvidenceDetailModal
          evidence={selectedEvidence}
          questionText={getQuestionText(selectedEvidence.relatedQuestionId)}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
};
