import React from 'react';
import { ResearchSession } from '../types';
import { DecisionReportView } from '../components/report/DecisionReportView';

interface DecisionReportPageProps {
  session: ResearchSession;
  onNavigateToEvidence?: () => void;
}

export const DecisionReportPage: React.FC<DecisionReportPageProps> = ({
  session,
  onNavigateToEvidence
}) => {
  return (
    <DecisionReportView
      session={session}
      onNavigateToEvidence={onNavigateToEvidence}
    />
  );
};
