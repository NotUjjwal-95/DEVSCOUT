import React from 'react';
import { CreateResearchDTO } from '../types';
import { NewResearchView } from '../components/new-research/NewResearchView';

interface NewResearchPageProps {
  onStart: (dto: CreateResearchDTO) => void;
  isStarting: boolean;
}

export const NewResearchPage: React.FC<NewResearchPageProps> = ({ onStart, isStarting }) => {
  return (
    <NewResearchView
      onStart={onStart}
      isStarting={isStarting}
    />
  );
};
