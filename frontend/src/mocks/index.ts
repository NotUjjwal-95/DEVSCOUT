import { ResearchSession, ResearchStageInfo } from '../types';
import { CANONICAL_WHITEBOARD_SESSION, DEFAULT_STAGES } from './whiteboardMock';
import { EVENT_PIPELINE_SESSION } from './eventPipelineMock';

export * from './whiteboardMock';
export * from './eventPipelineMock';

export const INITIAL_RESEARCH_STAGES: ResearchStageInfo[] = [
  { id: 'requirement_analysis', name: 'Requirement Analysis', description: 'Decompose constraints, concurrency targets, and state models', status: 'queued' },
  { id: 'research_planning', name: 'Research Planning', description: 'Formulate architectural questions and evidence criteria', status: 'queued' },
  { id: 'task_generation', name: 'Task Generation', description: 'Spin up source-directed probes for Web, GitHub, and RAG', status: 'queued' },
  { id: 'web_research', name: 'Web Research', description: 'Crawl official technical documentation, RFCs, and peer benchmarks', status: 'queued' },
  { id: 'github_research', name: 'GitHub Research', description: 'Audit production repositories, library activity, and open issues', status: 'queued' },
  { id: 'rag_research', name: 'RAG Research', description: 'Query DEVSCOUT curated engineering knowledge corpus', status: 'queued' },
  { id: 'evidence_processing', name: 'Evidence Processing', description: 'Normalize snippets, verify peer-reviewed claims, deduplicate', status: 'queued' },
  { id: 'decision_analysis', name: 'Decision Analysis', description: 'Synthesize trade-off matrix, fit criteria, and recommendation', status: 'queued' },
];

export const MOCK_RESEARCH_SESSIONS: ResearchSession[] = [
  CANONICAL_WHITEBOARD_SESSION,
  EVENT_PIPELINE_SESSION
];
