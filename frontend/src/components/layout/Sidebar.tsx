import React from 'react';
import {
  Compass,
  Plus,
  Cpu,
  Layers,
  FileText,
  History,
  Settings,
  HelpCircle,
  ChevronRight,
  GitFork,
  Radio
} from 'lucide-react';
import { ResearchSession } from '../../types/research';

export type MainView = 'new' | 'workspace' | 'evidence' | 'report' | 'history' | 'settings';

interface SidebarProps {
  currentView: MainView;
  onNavigate: (view: MainView) => void;
  activeSession: ResearchSession | null;
  allSessions: ResearchSession[];
  onSelectSession: (id: string) => void;
  onOpenHelp: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  activeSession,
  allSessions,
  onSelectSession,
  onOpenHelp,
  isOpenMobile,
  onCloseMobile
}) => {
  const isRunning = activeSession ? (
    activeSession.state === 'planning' ||
    activeSession.state === 'researching' ||
    activeSession.state === 'processing'
  ) : false;

  const getStateLabel = () => {
    if (!activeSession) return 'IDLE';
    const state = activeSession.state || activeSession.status;
    switch (state) {
      case 'planning': return 'PLANNING';
      case 'researching': return 'RESEARCHING';
      case 'processing': return 'PROCESSING';
      case 'completed': return 'COMPLETED';
      case 'failed': return 'FAILED';
      default: return 'IDLE';
    }
  };

  const navItems: { view: MainView; label: string; icon: React.ReactNode; badge?: number | string }[] = [
    {
      view: 'workspace',
      label: 'Workspace',
      icon: <Cpu className="w-4 h-4" />,
      badge: isRunning ? 'LIVE' : undefined
    },
    {
      view: 'evidence',
      label: 'Evidence',
      icon: <Layers className="w-4 h-4" />,
      badge: activeSession ? activeSession.evidence.length : undefined
    },
    {
      view: 'report',
      label: 'Decision Report',
      icon: <FileText className="w-4 h-4" />
    },
    {
      view: 'history',
      label: 'History',
      icon: <History className="w-4 h-4" />,
      badge: allSessions.length
    }
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-xs lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-[#0A0E17] border-r border-slate-800 flex flex-col justify-between transition-transform duration-200 lg:translate-x-0 ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top: Brand & Primary CTA */}
        <div className="p-4 space-y-4">
          {/* Brand lockup */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                onNavigate('new');
                onCloseMobile();
              }}
              className="flex items-center gap-2.5 text-left group focus:outline-hidden"
            >
              <div className="w-8 h-8 rounded bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 group-hover:border-blue-400 transition-colors">
                <Compass className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <span className="text-sm font-bold tracking-tight text-white block font-mono">
                  DEVSCOUT
                </span>
                <span className="text-[10px] text-slate-400 block font-sans tracking-wide">
                  Technical Decision Engine
                </span>
              </div>
            </button>
          </div>

          {/* New Research CTA */}
          <button
            onClick={() => {
              onNavigate('new');
              onCloseMobile();
            }}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-md transition-all shadow-xs ${
              currentView === 'new'
                ? 'bg-blue-600 text-white shadow-blue-900/30'
                : 'bg-blue-600/15 hover:bg-blue-600 text-blue-200 hover:text-white border border-blue-500/30 hover:border-blue-500'
            }`}
          >
            <Plus className="w-4 h-4" />
            <span>+ New Research</span>
          </button>

          {/* Active Project Switcher Chip */}
          {activeSession && (
            <div className="p-2.5 bg-slate-900/70 border border-slate-800/90 rounded-md space-y-1">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>ACTIVE SPIKE</span>
                <span className={`inline-flex items-center gap-1 ${
                  isRunning ? 'text-blue-400' :
                  activeSession.state === 'completed' || activeSession.status === 'completed' ? 'text-emerald-400' :
                  activeSession.state === 'failed' ? 'text-rose-400' : 'text-slate-400'
                }`}>
                  {isRunning && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />}
                  {getStateLabel()}
                </span>
              </div>
              <p className="text-xs font-medium text-slate-200 truncate font-sans" title={activeSession.projectName}>
                {activeSession.projectName}
              </p>
              <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1 pt-0.5">
                <span>{activeSession.scale || activeSession.requirementAnalysis?.targetScale}</span>
              </div>
            </div>
          )}

          {/* Main Navigation Items */}
          <nav className="space-y-1 pt-1">
            <span className="block text-[10px] font-mono uppercase tracking-wider text-slate-400 px-2.5 py-1">
              Workspace Areas
            </span>

            {navItems.map((item) => {
              const isActive = currentView === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => {
                    onNavigate(item.view);
                    onCloseMobile();
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>

                  {item.badge !== undefined && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                        item.badge === 'LIVE'
                          ? 'bg-blue-950 text-blue-400 border border-blue-800 animate-pulse font-bold'
                          : 'text-slate-400 bg-slate-900 border border-slate-800'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Settings & Help */}
        <div className="p-3 border-t border-slate-800/80 space-y-1 bg-[#090D15]">
          <button
            onClick={() => {
              onNavigate('settings');
              onCloseMobile();
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-md transition-colors ${
              currentView === 'settings'
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <Settings className="w-4 h-4 text-slate-400" />
            <span>Settings</span>
          </button>

          <button
            onClick={() => {
              onOpenHelp();
              onCloseMobile();
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 rounded-md transition-colors"
          >
            <HelpCircle className="w-4 h-4 text-slate-400" />
            <span>Methodology & Help</span>
          </button>

          <div className="pt-2 text-[10px] text-slate-400 px-3 font-sans leading-tight">
            "Research the stack. Understand the trade-offs. Build with confidence."
          </div>
        </div>
      </aside>
    </>
  );
};
