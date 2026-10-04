import React from 'react';
import { ResearchSession } from '../types';
import { WorkspaceView } from '../components/workspace/WorkspaceView';

interface WorkspacePageProps {
  session: ResearchSession;
  onFastForward: () => void;
  onCancel: () => void;
  onNavigateToReport: () => void;
  onNavigateToEvidence: () => void;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  session,
  onFastForward,
  onCancel,
  onNavigateToReport,
  onNavigateToEvidence
}) => {
  return (
    <WorkspaceView
      session={session}
      onFastForward={onFastForward}
      onCancel={onCancel}
      onNavigateToReport={onNavigateToReport}
      onNavigateToEvidence={onNavigateToEvidence}
    />
  );
};
