import React from 'react';
import { SettingsView } from '../components/settings/SettingsView';

interface SettingsPageProps {
  onResetSeed: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onResetSeed }) => {
  return <SettingsView onResetSeed={onResetSeed} />;
};
