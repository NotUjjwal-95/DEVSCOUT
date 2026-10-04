import React from 'react';
import { ResearchSession } from '../types';
import { ResearchHistoryView } from '../components/history/ResearchHistoryView';

interface HistoryPageProps {
  sessions: ResearchSession[];
  onOpenSession: (sessionId: string, targetView: 'workspace' | 'report' | 'evidence') => void;
  onDeleteSession: (sessionId: string) => void;
  onStartNew: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  sessions,
  onOpenSession,
  onDeleteSession,
  onStartNew
}) => {
  return (
    <ResearchHistoryView
      sessions={sessions}
      onOpenSession={onOpenSession}
      onDeleteSession={onDeleteSession}
      onStartNew={onStartNew}
    />
  );
};
