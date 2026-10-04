/**
 * Core DEVSCOUT Domain Data Models
 * Designed for 1:1 serialization with the DEVSCOUT Python Backend REST API
 */

export type SessionState = 'idle' | 'planning' | 'researching' | 'processing' | 'completed' | 'failed';

export type EvidenceSourceType = 'web' | 'github' | 'rag';

export type ResearchStageId =
  | 'requirement_analysis'
  | 'research_planning'
  | 'task_generation'
  | 'web_research'
  | 'github_research'
  | 'rag_research'
  | 'evidence_processing'
  | 'decision_analysis';

export interface RequirementAnalysis {
  problemStatement: string;
  coreObjective: string;
  targetScale: string;
  budgetTier: string;
  technologies: string[];
  hardConstraints: string[];
  preferences: string[];
  technicalDomain: string;
  concurrencyModel?: string;
  latencySla?: string;
  deploymentTarget?: string;
  teamSize?: string;
  existingStack?: string;
}

export interface ResearchTask {
  id: string;
  questionId: string;
  title: string;
  description: string;
  sourceType: EvidenceSourceType;
  status: 'queued' | 'running' | 'completed' | 'failed';
  searchQuery?: string;
  itemsFoundCount?: number;
  startedAt?: string;
  completedAt?: string;

  // Aliases for UI binding
  query?: string;
  source?: EvidenceSourceType;
}

export interface ResearchQuestion {
  id: string;
  question: string;
  priority: 'high' | 'medium' | 'low' | 'HIGH' | 'MEDIUM' | 'LOW';
  sources: EvidenceSourceType[];
  rationale: string;
  tasks: ResearchTask[];
  evidenceIds: string[];

  // Alias for UI binding
  why?: string;
}

export interface ResearchPlan {
  id: string;
  generatedAt: string;
  questions: ResearchQuestion[];
  totalTasks: number;
  targetedSources: EvidenceSourceType[];
  strategySummary: string;
}

export interface WebResearchResult {
  id: string;
  title: string;
  domain: string;
  url: string;
  snippet: string;
  fullQuote?: string;
  section?: string;
  citationIndex?: number;
  publishedDate?: string;
  confidenceScore?: number;
}

export interface GitHubResearchResult {
  id: string;
  owner: string;
  repo: string;
  fullName: string;
  description: string;
  language: string;
  stars: number;
  forks: number;
  openIssues: number;
  lastUpdated: string;
  url: string;
  license: string;
  commitFrequency: string;
  recentRelease: string;
  relevanceToArchitecture: string;

  // Aliases for UI binding
  name?: string;
  whyRelevant?: string;
}

export interface Evidence {
  id: string;
  sourceType: EvidenceSourceType;
  title: string;
  domain: string;
  url: string;
  snippet: string;
  fullQuote?: string;
  relatedQuestionId: string;
  relevance: 'primary' | 'high' | 'benchmark' | 'medium';
  verified: boolean;
  timestamp: string;
  webDetails?: WebResearchResult;
  githubDetails?: GitHubResearchResult;
  metadata?: Record<string, string | number>;
}

export interface RecommendationWhyPoint {
  point: string;
  evidenceIds: string[];
}

export interface DecisionAlternative {
  title: string;
  fitLevel: 'high' | 'medium' | 'low' | 'transport';
  summary: string;
  pros: string[];
  cons: string[];
  verdict: string;
  evidenceIds: string[];
}

export interface DecisionTradeoff {
  dimension: string;
  analysis: string;
  winner: string;
  evidenceIds: string[];
}

export interface TechnicalConsideration {
  category: string;
  guidance: string;
  actionableRule: string;
}

export interface DecisionReport {
  id: string;
  sessionId: string;
  generatedAt: string;
  executiveSummary: string;
  recommendedApproach: {
    title: string;
    fitLevel: 'high' | 'moderate' | 'conditional';
    architectureSummary: string;
    whyItFits: RecommendationWhyPoint[];
  };
  alternatives: DecisionAlternative[];
  tradeoffs: DecisionTradeoff[];
  technicalConsiderations: TechnicalConsideration[];
  sourcesSummary: {
    webCount: number;
    githubCount: number;
    ragCount: number;
    primaryDocs: string[];
  };
}

export interface ResearchStageInfo {
  id: ResearchStageId;
  name: string;
  description: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
}

export interface ResearchEvent {
  id: string;
  timestamp: string;
  stageId: ResearchStageId;
  message: string;
  type: 'info' | 'success' | 'warning' | 'artifact';
  detail?: string;
}

export interface ResearchSession {
  id: string;
  projectName: string;
  objective: string;
  state: SessionState;
  currentStage: ResearchStageId;
  currentStageIndex: number;
  createdAt: string;
  updatedAt: string;
  requirementAnalysis: RequirementAnalysis;
  plan: ResearchPlan | null;
  stages: ResearchStageInfo[];
  events: ResearchEvent[];
  evidence: Evidence[];
  repositories: GitHubResearchResult[];
  report: DecisionReport | null;

  // Convenience aliases for backward compatibility and UI binding
  status?: SessionState;
  scale?: string;
  budget?: string;
  technologies?: string[];
  constraints?: string[];
  preferences?: string[];
  activityEvents?: ResearchEvent[];
  githubRepos?: GitHubResearchResult[];
  questions?: ResearchQuestion[];
}

export interface CreateResearchDTO {
  objective: string;
  technologies: string[];
  constraints: string[];
  scale: string;
  budget: string;
  preferences: string[];
  advanced?: {
    deploymentTarget?: string;
    latencyTarget?: string;
    teamSize?: string;
    existingStack?: string;
  };
}

export interface ResearchStartResponse {
  id?: string;
  researchId?: string;
  research_id?: string;
  session?: ResearchSession;
}

export interface ResearchStatusResponse {
  id: string;
  state: SessionState;
  currentStage: ResearchStageId;
  currentStageIndex: number;
  totalStages: number;
  completedStages: number;
  evidenceCount: number;
  repositoriesCount: number;
  isComplete: boolean;
  hasReport: boolean;
}

export interface EvidenceFilter {
  sourceType?: EvidenceSourceType | 'all';
  query?: string;
  sortBy?: 'relevance' | 'newest' | 'domain';
}

export interface ResearchSessionSummary {
  id: string;
  projectName: string;
  objective: string;
  state: SessionState;
  createdAt: string;
  updatedAt: string;
  sourcesCount: number;
  repositoriesCount: number;
  scale: string;
}
