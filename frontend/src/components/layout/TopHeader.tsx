import React from 'react';
import { MainView } from './Sidebar';
import { ResearchSession } from '../../types/research';
import { Menu, Plus, ChevronRight, Cpu, FileText, Layers, ShieldCheck } from 'lucide-react';

interface TopHeaderProps {
  currentView: MainView;
  activeSession: ResearchSession | null;
  onNavigate: (view: MainView) => void;
  onToggleMobileMenu: () => void;
  allSessions: ResearchSession[];
  onSelectSession: (id: string) => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  currentView,
  activeSession,
  onNavigate,
  onToggleMobileMenu,
  allSessions,
  onSelectSession
}) => {
  const getViewTitle = () => {
    switch (currentView) {
      case 'new':
        return 'New Technical Research';
      case 'workspace':
        return 'Research Workspace';
      case 'evidence':
        return 'Evidence Explorer';
      case 'report':
        return 'Decision Report';
      case 'history':
        return 'Research History';
      case 'settings':
        return 'Engine Settings';
      default:
        return 'DEVSCOUT';
    }
  };

  return (
    <header className="sticky top-0 z-30 h-14 bg-[#0B0F17]/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Zone 1: Mobile toggle & Breadcrumb Trail */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleMobileMenu}
          aria-label="Open navigation sidebar"
          className="lg:hidden p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-md"
        >
          <Menu className="w-5 h-5" />
        </button>

        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs font-mono truncate">
          <button
            onClick={() => onNavigate('new')}
            className="text-slate-400 hover:text-slate-200 transition-colors whitespace-nowrap"
          >
            DEVSCOUT
          </button>

          <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />

          <span className="text-slate-300 font-semibold truncate whitespace-nowrap">
            {getViewTitle()}
          </span>

          {activeSession && currentView !== 'new' && currentView !== 'history' && currentView !== 'settings' && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0 hidden sm:inline" />
              <span className="text-slate-400 truncate max-w-[200px] hidden sm:inline" title={activeSession.projectName}>
                {activeSession.projectName}
              </span>
            </>
          )}
        </nav>
      </div>

      {/* Zone 2: Project Switcher Dropdown (Single-Line Control) */}
      <div className="hidden md:flex items-center gap-2 shrink-0">
        {allSessions.length > 1 && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="font-mono text-[11px] text-slate-400">SPIKE:</span>
            <select
              value={activeSession?.id || ''}
              onChange={(e) => onSelectSession(e.target.value)}
              aria-label="Switch active research spike"
              className="bg-[#101522] border border-slate-700/80 rounded-md px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-hidden focus:border-blue-500 max-w-[220px] truncate"
            >
              {allSessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.projectName}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Zone 3: 1-2 Primary Actions */}
      <div className="flex items-center gap-2 shrink-0">
        {currentView !== 'new' && (
          <button
            onClick={() => onNavigate('new')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-md shadow-xs transition-colors whitespace-nowrap"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Research</span>
            <span className="sm:hidden">New</span>
          </button>
        )}
      </div>
    </header>
  );
};
