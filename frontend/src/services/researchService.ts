import {
  ResearchSession,
  CreateResearchDTO,
  ResearchStatusResponse,
  ResearchTask,
  Evidence,
  GitHubResearchResult,
  DecisionReport,
  EvidenceFilter,
  ResearchSessionSummary,
  ResearchStageInfo,
  ResearchStageId,
  RequirementAnalysis,
  ResearchStartResponse
} from '../types';
import {
  MOCK_RESEARCH_SESSIONS,
  INITIAL_RESEARCH_STAGES,
  WHITEBOARD_QUESTIONS,
  WHITEBOARD_EVIDENCE,
  WHITEBOARD_REPOSITORIES,
  WHITEBOARD_REPORT
} from '../mocks';

const STORAGE_KEY = 'devscout_research_sessions_v2';
const SETTINGS_KEY = 'devscout_settings_v2';
const DEFAULT_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const DEFAULT_USE_LIVE_BACKEND = import.meta.env.VITE_USE_LIVE_BACKEND === 'true';

export interface DevscoutSettings {
  apiBaseUrl: string;
  useLiveBackend: boolean;
  researchDepth: 'standard' | 'deep' | 'exhaustive';
  enableWebSearch: boolean;
  enableGithubAudit: boolean;
  enableInternalRag: boolean;
}

export class ResearchApiError extends Error {
  public readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ResearchApiError';
    this.status = status;
  }
}

const DEFAULT_SETTINGS: DevscoutSettings = {
  apiBaseUrl: DEFAULT_API_BASE_URL,
  useLiveBackend: DEFAULT_USE_LIVE_BACKEND,
  researchDepth: 'deep',
  enableWebSearch: true,
  enableGithubAudit: true,
  enableInternalRag: true,
};

class ResearchService {
  private sessions: ResearchSession[] = [];
  private activeTimers: Map<string, NodeJS.Timeout[]> = new Map();
  private activePolls: Map<string, number> = new Map();

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.sessions = JSON.parse(stored);
      } else {
        this.sessions = JSON.parse(JSON.stringify(MOCK_RESEARCH_SESSIONS));
        this.saveToStorage();
      }
    } catch {
      this.sessions = JSON.parse(JSON.stringify(MOCK_RESEARCH_SESSIONS));
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.sessions));
    } catch {
      // quota or local storage restriction
    }
  }

  public getSettings(): DevscoutSettings {
    try {
      const stored = localStorage.getItem(SETTINGS_KEY);
      return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  }

  public saveSettings(settings: DevscoutSettings): void {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      // ignore
    }
  }

  /**
   * createResearch()
   * Initiates a new technical investigation spike.
   * Maps 1:1 to POST /api/v1/research/start in the Python backend.
   */
  public async createResearch(
    input: CreateResearchDTO,
    onProgress?: (session: ResearchSession) => void,
    onError?: (error: Error) => void
  ): Promise<ResearchSession> {
    if (this.getSettings().useLiveBackend) {
      return this.createLiveResearch(input, onProgress, onError);
    }

    const id = `res-${Date.now()}`;
    const now = new Date().toISOString();

    const projectName = input.objective.length > 55
      ? `${input.objective.slice(0, 52).trim()}...`
      : input.objective;

    const stages: ResearchStageInfo[] = INITIAL_RESEARCH_STAGES.map((s, idx) => ({
      ...s,
      status: idx === 0 ? 'running' : 'queued',
      startedAt: idx === 0 ? now : undefined
    }));

    const requirementAnalysis: RequirementAnalysis = {
      problemStatement: input.objective,
      coreObjective: input.objective,
      targetScale: input.scale || '~1,000 concurrent users',
      budgetTier: input.budget || 'Low / Bootstrapped',
      technologies: input.technologies,
      hardConstraints: input.constraints,
      preferences: input.preferences,
      technicalDomain: 'Distributed Systems & Architecture Trade-offs',
      latencySla: input.advanced?.latencyTarget,
      deploymentTarget: input.advanced?.deploymentTarget,
      teamSize: input.advanced?.teamSize,
      existingStack: input.advanced?.existingStack
    };

    const newSession: ResearchSession = {
      id,
      projectName,
      objective: input.objective,
      state: 'planning',
      currentStage: 'requirement_analysis',
      currentStageIndex: 0,
      createdAt: now,
      updatedAt: now,
      requirementAnalysis,
      plan: null,
      stages,
      events: [
        {
          id: `ev-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'requirement_analysis',
          type: 'info',
          message: `Initiating research engine: "${input.objective.slice(0, 70)}..."`
        }
      ],
      evidence: [],
      repositories: [],
      report: null
    };

    this.sessions.unshift(newSession);
    this.saveToStorage();

    if (onProgress) {
      onProgress(JSON.parse(JSON.stringify(newSession)));
    }

    this.simulatePipelineExecution(id, input, onProgress);
    return JSON.parse(JSON.stringify(newSession));
  }

  /**
   * getResearchSession()
   * Retrieves full research session document.
   * Maps to GET /api/v1/research/{id}
   */
  public async getResearchSession(id: string): Promise<ResearchSession | null> {
    if (this.getSettings().useLiveBackend) {
      return this.request<ResearchSession>(`/research/${encodeURIComponent(id)}`);
    }

    const session = this.sessions.find(s => s.id === id);
    return session ? JSON.parse(JSON.stringify(session)) : null;
  }

  /**
   * getResearchStatus()
   * Polling endpoint for execution status and stage progress.
   * Maps to GET /api/v1/research/{id}/status
   */
  public async getResearchStatus(id: string): Promise<ResearchStatusResponse | null> {
    if (this.getSettings().useLiveBackend) {
      return this.request<ResearchStatusResponse>(`/research/${encodeURIComponent(id)}/status`);
    }

    const session = await this.getResearchSession(id);
    if (!session) return null;

    const completedStages = session.stages.filter(s => s.status === 'completed').length;
    return {
      id: session.id,
      state: session.state,
      currentStage: session.currentStage,
      currentStageIndex: session.currentStageIndex,
      totalStages: session.stages.length,
      completedStages,
      evidenceCount: session.evidence.length,
      repositoriesCount: session.repositories.length,
      isComplete: session.state === 'completed',
      hasReport: session.report !== null
    };
  }

  /**
   * getResearchTasks()
   * Retrieves all generated research tasks for a session.
   * Maps to GET /api/v1/research/{id}/tasks
   */
  public async getResearchTasks(id: string): Promise<ResearchTask[]> {
    if (this.getSettings().useLiveBackend) {
      const response = await this.request<ResearchTask[] | { tasks: ResearchTask[] }>(
        `/research/${encodeURIComponent(id)}/tasks`
      );
      return Array.isArray(response) ? response : response.tasks;
    }

    const session = await this.getResearchSession(id);
    if (!session || !session.plan) return [];
    return session.plan.questions.flatMap(q => q.tasks);
  }

  /**
   * getEvidence()
   * Retrieves and filters evidence items.
   * Maps to GET /api/v1/research/{id}/evidence
   */
  public async getEvidence(id: string, filter?: EvidenceFilter): Promise<Evidence[]> {
    if (this.getSettings().useLiveBackend) {
      const response = await this.request<Evidence[] | { evidence: Evidence[] }>(
        `/research/${encodeURIComponent(id)}/evidence`
      );
      return this.filterEvidence(Array.isArray(response) ? response : response.evidence, filter);
    }

    const session = await this.getResearchSession(id);
    if (!session) return [];

    let items = [...session.evidence];

    if (filter?.sourceType && filter.sourceType !== 'all') {
      items = items.filter(e => e.sourceType === filter.sourceType);
    }

    if (filter?.query && filter.query.trim()) {
      const q = filter.query.toLowerCase().trim();
      items = items.filter(
        e =>
          e.title.toLowerCase().includes(q) ||
          e.snippet.toLowerCase().includes(q) ||
          e.domain.toLowerCase().includes(q)
      );
    }

    if (filter?.sortBy === 'relevance') {
      const order = { primary: 4, benchmark: 3, high: 2, medium: 1 };
      items.sort((a, b) => (order[b.relevance] || 0) - (order[a.relevance] || 0));
    } else if (filter?.sortBy === 'newest') {
      items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } else if (filter?.sortBy === 'domain') {
      items.sort((a, b) => a.domain.localeCompare(b.domain));
    }

    return items;
  }

  /**
   * getRepositories()
   * Retrieves inspected GitHub repositories.
   * Maps to GET /api/v1/research/{id}/repositories
   */
  public async getRepositories(id: string): Promise<GitHubResearchResult[]> {
    if (this.getSettings().useLiveBackend) {
      const response = await this.request<GitHubResearchResult[] | { repositories: GitHubResearchResult[] }>(
        `/research/${encodeURIComponent(id)}/repositories`
      );
      return Array.isArray(response) ? response : response.repositories;
    }

    const session = await this.getResearchSession(id);
    return session?.repositories || [];
  }

  /**
   * getDecisionReport()
   * Retrieves synthesized architectural decision report.
   * Maps to GET /api/v1/research/{id}/report
   */
  public async getDecisionReport(id: string): Promise<DecisionReport | null> {
    if (this.getSettings().useLiveBackend) {
      return this.request<DecisionReport>(`/research/${encodeURIComponent(id)}/report`);
    }

    const session = await this.getResearchSession(id);
    return session?.report || null;
  }

  /**
   * getResearchHistory()
   * Retrieves session summaries for history list.
   * Maps to GET /api/v1/research/history
   */
  public async getResearchHistory(): Promise<ResearchSessionSummary[]> {
    if (this.getSettings().useLiveBackend) {
      const response = await this.request<ResearchSessionSummary[] | { history: ResearchSessionSummary[] }>(
        '/research/history'
      );
      return Array.isArray(response) ? response : response.history;
    }

    return this.sessions
      .map(s => ({
        id: s.id,
        projectName: s.projectName,
        objective: s.objective,
        state: s.state,
        createdAt: s.createdAt,
        updatedAt: s.updatedAt,
        sourcesCount: s.evidence.length,
        repositoriesCount: s.repositories.length,
        scale: s.requirementAnalysis.targetScale
      }))
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }

  public async getAllSessions(): Promise<ResearchSession[]> {
    if (this.getSettings().useLiveBackend) {
      const history = await this.getResearchHistory();
      const sessions = await Promise.all(history.map(item => this.getResearchSession(item.id)));
      return sessions.filter((session): session is ResearchSession => session !== null);
    }

    return [...this.sessions].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  public async deleteResearchSession(id: string): Promise<void> {
    if (this.getSettings().useLiveBackend) {
      throw new ResearchApiError('Deleting research sessions is not supported by the FastAPI contract.');
    }

    this.cancelResearch(id);
    this.sessions = this.sessions.filter(s => s.id !== id);
    this.saveToStorage();
  }

  public cancelResearch(id: string): boolean {
    const poll = this.activePolls.get(id);
    if (poll !== undefined) {
      window.clearInterval(poll);
      this.activePolls.delete(id);
    }
    if (this.getSettings().useLiveBackend) {
      return false;
    }

    const timers = this.activeTimers.get(id);
    if (timers) {
      timers.forEach(clearTimeout);
      this.activeTimers.delete(id);
    }
    const session = this.sessions.find(s => s.id === id);
    if (session && (session.state === 'planning' || session.state === 'researching' || session.state === 'processing')) {
      session.state = 'failed';
      session.events.push({
        id: `ev-halt-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        stageId: session.currentStage,
        type: 'warning',
        message: 'Research pipeline halted by user'
      });
      this.saveToStorage();
    }
    return true;
  }

  public async fastForwardResearch(id: string): Promise<ResearchSession | null> {
    if (this.getSettings().useLiveBackend) {
      return this.getResearchSession(id);
    }

    const timers = this.activeTimers.get(id);
    if (timers) {
      timers.forEach(clearTimeout);
      this.activeTimers.delete(id);
    }
    const session = this.sessions.find(s => s.id === id);
    if (!session) return null;

    session.state = 'completed';
    session.currentStage = 'decision_analysis';
    session.currentStageIndex = session.stages.length - 1;
    session.stages = session.stages.map(s => ({
      ...s,
      status: 'completed',
      durationSeconds: s.durationSeconds || Math.floor(Math.random() * 5) + 2
    }));

    if (!session.plan) {
      session.plan = {
        id: `plan-${session.id}`,
        generatedAt: new Date().toISOString(),
        questions: WHITEBOARD_QUESTIONS,
        totalTasks: WHITEBOARD_QUESTIONS.flatMap(q => q.tasks).length,
        targetedSources: ['web', 'github', 'rag'],
        strategySummary: 'Triangulate official web specifications with GitHub code patterns and RAG distributed systems corpus.'
      };
    }

    if (session.evidence.length === 0) {
      session.evidence = WHITEBOARD_EVIDENCE;
    }

    if (session.repositories.length === 0) {
      session.repositories = WHITEBOARD_REPOSITORIES;
    }

    if (!session.report) {
      session.report = {
        ...WHITEBOARD_REPORT,
        id: `rep-${session.id}`,
        sessionId: session.id
      };
    }

    session.events.push({
      id: `ev-done-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      stageId: 'decision_analysis',
      type: 'success',
      message: 'Decision synthesis finalized. All trade-offs grounded in multi-source evidence.'
    });

    this.saveToStorage();
    return JSON.parse(JSON.stringify(session));
  }

  public resetAllToSeed(): void {
    if (this.getSettings().useLiveBackend) {
      return;
    }
    this.sessions = JSON.parse(JSON.stringify(MOCK_RESEARCH_SESSIONS));
    this.saveToStorage();
  }

  private simulatePipelineExecution(
    sessionId: string,
    input: CreateResearchDTO,
    onProgress?: (session: ResearchSession) => void
  ): void {
    const timers: NodeJS.Timeout[] = [];
    const delays = [1200, 2400, 3600, 5000, 6800, 8600, 10400, 12400];

    const stages: ResearchStageId[] = [
      'requirement_analysis',
      'research_planning',
      'task_generation',
      'web_research',
      'github_research',
      'rag_research',
      'evidence_processing',
      'decision_analysis'
    ];

    // Stage 0: requirement_analysis
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'planning';
        session.currentStage = 'research_planning';
        session.currentStageIndex = 1;
        session.stages[0].status = 'completed';
        session.stages[0].durationSeconds = 1;
        session.stages[1].status = 'running';

        session.events.push({
          id: `ev-0-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'requirement_analysis',
          type: 'info',
          message: `Identified ${session.requirementAnalysis.hardConstraints.length || 4} hard constraints and verified scale target (${session.requirementAnalysis.targetScale})`
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[0])
    );

    // Stage 1: research_planning
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'planning';
        session.currentStage = 'task_generation';
        session.currentStageIndex = 2;
        session.stages[1].status = 'completed';
        session.stages[1].durationSeconds = 1;
        session.stages[2].status = 'running';

        session.plan = {
          id: `plan-${sessionId}`,
          generatedAt: new Date().toISOString(),
          questions: WHITEBOARD_QUESTIONS.slice(0, 2),
          totalTasks: 4,
          targetedSources: ['web', 'github', 'rag'],
          strategySummary: 'Deconstruct synchronization layer and transport protocols.'
        };

        session.events.push({
          id: `ev-1-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'research_planning',
          type: 'info',
          message: `Generated ${WHITEBOARD_QUESTIONS.length} architectural research questions`
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[1])
    );

    // Stage 2: task_generation
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'researching';
        session.currentStage = 'web_research';
        session.currentStageIndex = 3;
        session.stages[2].status = 'completed';
        session.stages[2].durationSeconds = 1;
        session.stages[3].status = 'running';

        if (session.plan) {
          session.plan.questions = WHITEBOARD_QUESTIONS;
          session.plan.totalTasks = WHITEBOARD_QUESTIONS.flatMap(q => q.tasks).length;
        }

        session.events.push({
          id: `ev-2-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'task_generation',
          type: 'info',
          message: 'Created 9 source-directed research tasks targeting official specs, benchmarks, and repos'
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[2])
    );

    // Stage 3: web_research
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'researching';
        session.currentStage = 'github_research';
        session.currentStageIndex = 4;
        session.stages[3].status = 'completed';
        session.stages[3].durationSeconds = 2;
        session.stages[4].status = 'running';

        const webItems = WHITEBOARD_EVIDENCE.filter(e => e.sourceType === 'web');
        session.evidence.push(...webItems);

        session.events.push({
          id: `ev-3-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'web_research',
          type: 'artifact',
          message: 'Indexed RFC 6455 and Yjs vector benchmark specifications'
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[3])
    );

    // Stage 4: github_research
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'researching';
        session.currentStage = 'rag_research';
        session.currentStageIndex = 5;
        session.stages[4].status = 'completed';
        session.stages[4].durationSeconds = 2;
        session.stages[5].status = 'running';

        session.repositories = WHITEBOARD_REPOSITORIES;
        const ghItems = WHITEBOARD_EVIDENCE.filter(e => e.sourceType === 'github');
        session.evidence.push(...ghItems);

        session.events.push({
          id: `ev-4-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'github_research',
          type: 'artifact',
          message: `Audited ${WHITEBOARD_REPOSITORIES.length} production repositories (gorilla/websocket, yjs, tldraw, y-websocket)`
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[4])
    );

    // Stage 5: rag_research
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'processing';
        session.currentStage = 'evidence_processing';
        session.currentStageIndex = 6;
        session.stages[5].status = 'completed';
        session.stages[5].durationSeconds = 2;
        session.stages[6].status = 'running';

        const ragItems = WHITEBOARD_EVIDENCE.filter(e => e.sourceType === 'rag');
        session.evidence.push(...ragItems);

        session.events.push({
          id: `ev-5-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'rag_research',
          type: 'info',
          message: 'Retrieved DEVSCOUT knowledge base patterns: OT vs CRDT trade-offs & Go fan-out hubs'
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[5])
    );

    // Stage 6: evidence_processing
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'processing';
        session.currentStage = 'decision_analysis';
        session.currentStageIndex = 7;
        session.stages[6].status = 'completed';
        session.stages[6].durationSeconds = 2;
        session.stages[7].status = 'running';

        session.events.push({
          id: `ev-6-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'evidence_processing',
          type: 'success',
          message: `Normalized and validated ${session.evidence.length} evidence items against primary standards`
        });

        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[6])
    );

    // Stage 7: decision_analysis -> completed
    timers.push(
      setTimeout(() => {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session || session.state === 'failed') return;
        session.state = 'completed';
        session.currentStage = 'decision_analysis';
        session.currentStageIndex = 7;
        session.stages[7].status = 'completed';
        session.stages[7].durationSeconds = 2;
        session.report = {
          ...WHITEBOARD_REPORT,
          id: `rep-${session.id}`,
          sessionId: session.id
        };

        session.events.push({
          id: `ev-7-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          stageId: 'decision_analysis',
          type: 'success',
          message: 'Decision Report generated: Recommended Approach grounded in 9 verified sources'
        });

        this.activeTimers.delete(sessionId);
        this.saveToStorage();
        if (onProgress) onProgress(JSON.parse(JSON.stringify(session)));
      }, delays[7])
    );

    this.activeTimers.set(sessionId, timers);
  }

  private async createLiveResearch(
    input: CreateResearchDTO,
    onProgress?: (session: ResearchSession) => void,
    onError?: (error: Error) => void
  ): Promise<ResearchSession> {
    const response = await this.request<ResearchStartResponse | ResearchSession>('/research/start', {
      method: 'POST',
      body: JSON.stringify(input)
    });
    const started = this.unwrapResponse(response);
    const sessionId = this.getResponseId(started);
    const initial = this.isResearchSession(started)
      ? started
      : await this.getResearchSession(sessionId);

    if (!initial) {
      throw new ResearchApiError(`Research "${sessionId}" was started but its session could not be loaded.`);
    }
    onProgress?.(initial);
    this.startPolling(sessionId, onProgress, onError);
    return initial;
  }

  private startPolling(
    id: string,
    onProgress?: (session: ResearchSession) => void,
    onError?: (error: Error) => void
  ): void {
    const existing = this.activePolls.get(id);
    if (existing !== undefined) window.clearInterval(existing);

    const poll = window.setInterval(async () => {
      try {
        const session = await this.getResearchSession(id);
        if (session) onProgress?.(session);
        const status = await this.getResearchStatus(id);
        if (status?.isComplete || status?.state === 'failed') {
          window.clearInterval(poll);
          this.activePolls.delete(id);
        }
      } catch (cause) {
        window.clearInterval(poll);
        this.activePolls.delete(id);
        const error = cause instanceof Error ? cause : new ResearchApiError('Research polling failed.');
        onError?.(error);
      }
    }, 2000);
    this.activePolls.set(id, poll);
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const { apiBaseUrl } = this.getSettings();
    const baseUrl = apiBaseUrl.replace(/\/+$/, '');
    let response: Response;
    try {
      response = await fetch(`${baseUrl}${path}`, {
        ...init,
        headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init.headers }
      });
    } catch {
      throw new ResearchApiError(`Unable to reach the research backend at ${baseUrl}.`);
    }

    const text = await response.text();
    let payload: unknown = undefined;
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = text;
      }
    }
    if (!response.ok) {
      const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
        ? String(payload.detail)
        : `Request failed with status ${response.status}.`;
      throw new ResearchApiError(detail, response.status);
    }
    return this.unwrapResponse(payload) as T;
  }

  private unwrapResponse<T>(payload: T): T {
    if (typeof payload === 'object' && payload !== null && 'data' in payload) {
      return (payload as T & { data: T }).data;
    }
    return payload;
  }

  private getResponseId(response: ResearchStartResponse | ResearchSession): string {
    if ('id' in response && typeof response.id === 'string') return response.id;
    if ('researchId' in response && typeof response.researchId === 'string') return response.researchId;
    if ('research_id' in response && typeof response.research_id === 'string') return response.research_id;
    throw new ResearchApiError('The research backend returned no session id.');
  }

  private isResearchSession(value: ResearchStartResponse | ResearchSession): value is ResearchSession {
    return 'objective' in value && 'state' in value && 'stages' in value;
  }

  private filterEvidence(items: Evidence[], filter?: EvidenceFilter): Evidence[] {
    let filtered = [...items];
    if (filter?.sourceType && filter.sourceType !== 'all') {
      filtered = filtered.filter(item => item.sourceType === filter.sourceType);
    }
    if (filter?.query?.trim()) {
      const query = filter.query.toLowerCase().trim();
      filtered = filtered.filter(item =>
        [item.title, item.snippet, item.domain].some(value => value.toLowerCase().includes(query))
      );
    }
    if (filter?.sortBy === 'relevance') {
      const order = { primary: 4, benchmark: 3, high: 2, medium: 1 };
      filtered.sort((a, b) => order[b.relevance] - order[a.relevance]);
    } else if (filter?.sortBy === 'newest') {
      filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } else if (filter?.sortBy === 'domain') {
      filtered.sort((a, b) => a.domain.localeCompare(b.domain));
    }
    return filtered;
  }
}

export const researchService = new ResearchService();
