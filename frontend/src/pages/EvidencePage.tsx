import React from 'react';
import { ResearchSession } from '../types';
import { EvidenceExplorerView } from '../components/evidence/EvidenceExplorerView';

interface EvidencePageProps {
  session: ResearchSession;
}

export const EvidencePage: React.FC<EvidencePageProps> = ({ session }) => {
  return <EvidenceExplorerView session={session} />;
};
