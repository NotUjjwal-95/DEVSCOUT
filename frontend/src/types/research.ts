export * from './index';

// Backward compatibility aliases if needed
export type SourceType = import('./index').EvidenceSourceType;
export type StageStatus = 'queued' | 'running' | 'completed' | 'failed';
export type ResearchStage = import('./index').ResearchStageInfo;
export type EvidenceItem = import('./index').Evidence;
export type GithubRepo = import('./index').GitHubResearchResult;
export type ResearchObjectiveInput = import('./index').CreateResearchDTO;
