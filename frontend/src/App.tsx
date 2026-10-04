/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { ResearchSession, CreateResearchDTO } from './types';
import { researchService } from './services/researchService';
import { Sidebar, MainView } from './components/layout/Sidebar';
import { TopHeader } from './components/layout/TopHeader';
import { NewResearchPage } from './pages/NewResearchPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvidencePage } from './pages/EvidencePage';
import { DecisionReportPage } from './pages/DecisionReportPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { HelpModal } from './components/help/HelpModal';

export default function App() {
  const [currentView, setCurrentView] = useState<MainView>('workspace');
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [isStarting, setIsStarting] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Load research sessions from service layer on mount
  useEffect(() => {
    const init = async () => {
      const all = await researchService.getAllSessions();
      setSessions(all);
      if (all.length > 0) {
        setActiveSessionId(all[0].id);
      }
    };
    init();
  }, []);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0] || null;

  // Handlers using typed service layer
  const handleStartResearch = async (dto: CreateResearchDTO) => {
    setIsStarting(true);
    try {
      const newSession = await researchService.createResearch(dto, (updated) => {
        setSessions(prev => {
          const index = prev.findIndex(s => s.id === updated.id);
          if (index !== -1) {
            const next = [...prev];
            next[index] = updated;
            return next;
          }
          return [updated, ...prev];
        });
      });

      setSessions(prev => [newSession, ...prev.filter(s => s.id !== newSession.id)]);
      setActiveSessionId(newSession.id);
      setCurrentView('workspace');
    } finally {
      setIsStarting(false);
    }
  };

  const handleFastForward = async () => {
    if (!activeSession) return;
    const completed = await researchService.fastForwardResearch(activeSession.id);
    if (completed) {
      setSessions(prev => prev.map(s => (s.id === completed.id ? completed : s)));
    }
  };

  const handleCancelResearch = () => {
    if (!activeSession) return;
    researchService.cancelResearch(activeSession.id);
    setSessions(prev =>
      prev.map(s => {
        if (s.id === activeSession.id) {
          return { ...s, state: 'failed', status: 'failed' };
        }
        return s;
      })
    );
  };

  const handleDeleteSession = async (id: string) => {
    await researchService.deleteResearchSession(id);
    const updated = await researchService.getAllSessions();
    setSessions(updated);
    if (activeSessionId === id && updated.length > 0) {
      setActiveSessionId(updated[0].id);
    }
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleOpenSession = (id: string, targetView: 'workspace' | 'report' | 'evidence') => {
    setActiveSessionId(id);
    setCurrentView(targetView);
  };

  const handleResetSeed = async () => {
    researchService.resetAllToSeed();
    const all = await researchService.getAllSessions();
    setSessions(all);
    if (all.length > 0) {
      setActiveSessionId(all[0].id);
    }
    setCurrentView('workspace');
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={setCurrentView}
        activeSession={activeSession}
        allSessions={sessions}
        onSelectSession={handleSelectSession}
        onOpenHelp={() => setIsHelpOpen(true)}
        isOpenMobile={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col min-h-screen flex-1">
        {/* Top Header */}
        <TopHeader
          currentView={currentView}
          activeSession={activeSession}
          onNavigate={setCurrentView}
          onToggleMobileMenu={() => setIsMobileMenuOpen(prev => !prev)}
          allSessions={sessions}
          onSelectSession={handleSelectSession}
        />

        {/* Viewport Canvas (1440px baseline presence) */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1440px] w-full mx-auto">
          {currentView === 'new' && (
            <NewResearchPage
              onStart={handleStartResearch}
              isStarting={isStarting}
            />
          )}

          {currentView === 'workspace' && activeSession && (
            <WorkspacePage
              session={activeSession}
              onFastForward={handleFastForward}
              onCancel={handleCancelResearch}
              onNavigateToReport={() => setCurrentView('report')}
              onNavigateToEvidence={() => setCurrentView('evidence')}
            />
          )}

          {currentView === 'workspace' && !activeSession && (
            <NewResearchPage
              onStart={handleStartResearch}
              isStarting={isStarting}
            />
          )}

          {currentView === 'evidence' && activeSession && (
            <EvidencePage session={activeSession} />
          )}

          {currentView === 'evidence' && !activeSession && (
            <div className="text-center py-20 text-slate-400">
              No active research session. Start a new research spike to explore evidence.
            </div>
          )}

          {currentView === 'report' && activeSession && (
            <DecisionReportPage
              session={activeSession}
              onNavigateToEvidence={() => setCurrentView('evidence')}
            />
          )}

          {currentView === 'report' && !activeSession && (
            <div className="text-center py-20 text-slate-400">
              No active decision report. Start a new research spike to generate one.
            </div>
          )}

          {currentView === 'history' && (
            <HistoryPage
              sessions={sessions}
              onOpenSession={handleOpenSession}
              onDeleteSession={handleDeleteSession}
              onStartNew={() => setCurrentView('new')}
            />
          )}

          {currentView === 'settings' && (
            <SettingsPage onResetSeed={handleResetSeed} />
          )}
        </main>
      </div>

      {/* Help & Methodology Modal */}
      <HelpModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </div>
  );
}
