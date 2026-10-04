import React from 'react';
import { GithubRepo } from '../../types/research';
import { Star, GitFork, AlertCircle, ExternalLink, Calendar, Activity, CheckCircle2 } from 'lucide-react';

interface GithubRepoCardProps {
  repo: GithubRepo;
}

const LANGUAGE_COLORS: Record<string, string> = {
  Go: '#00ADD8',
  TypeScript: '#3178C6',
  JavaScript: '#F7DF1E',
  'C++': '#F34B7D',
  Rust: '#DEA584',
  Python: '#3572A5'
};

export const GithubRepoCard: React.FC<GithubRepoCardProps> = ({ repo }) => {
  const langColor = LANGUAGE_COLORS[repo.language] || '#94A3B8';

  return (
    <article className="bg-[#101522] border border-slate-800/80 hover:border-slate-700 rounded-lg p-5 transition-colors flex flex-col justify-between">
      <div>
        {/* Repo owner/name & link */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="space-y-0.5">
            <span className="text-xs font-mono text-slate-400 block">
              {repo.owner} /
            </span>
            <h3 className="text-base font-semibold font-mono text-blue-400 hover:text-blue-300">
              <a
                href={repo.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 focus:outline-hidden focus:underline"
              >
                {repo.name || repo.repo}
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
              </a>
            </h3>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: langColor }} />
            <span>{repo.language}</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-slate-300 leading-relaxed mb-4 font-sans line-clamp-2">
          {repo.description}
        </p>

        {/* Why relevant context */}
        <div className="p-3 bg-slate-950/60 border-l-2 border-emerald-500 rounded-r-md text-xs text-slate-300 mb-4">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 mb-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>RELEVANCE TO ARCHITECTURE</span>
          </div>
          <p className="text-[12px] text-slate-300 leading-snug">
            {repo.whyRelevant || repo.relevanceToArchitecture}
          </p>
        </div>
      </div>

      <div>
        {/* Activity & Maintenance Signals (stars alone != quality) */}
        <div className="grid grid-cols-2 gap-2 text-xs py-2.5 border-t border-slate-800/60 font-mono mb-3">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-[11px] text-slate-300">{repo.commitFrequency}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-300">Updated {repo.lastUpdated}</span>
          </div>
        </div>

        {/* Numeric stats with tabular numbers */}
        <div className="flex items-center justify-between text-xs text-slate-400 font-mono tabular-nums pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1 text-slate-300" title="GitHub Stars">
              <Star className="w-3.5 h-3.5 text-amber-400" />
              {repo.stars.toLocaleString()}
            </span>
            <span className="inline-flex items-center gap-1 text-slate-400" title="Forks">
              <GitFork className="w-3.5 h-3.5" />
              {repo.forks.toLocaleString()}
            </span>
            <span className="inline-flex items-center gap-1 text-slate-400" title="Open Issues">
              <AlertCircle className="w-3.5 h-3.5" />
              {repo.openIssues.toLocaleString()}
            </span>
          </div>

          <span className="text-[11px] text-slate-400 font-mono">
            {repo.license}
          </span>
        </div>
      </div>
    </article>
  );
};
