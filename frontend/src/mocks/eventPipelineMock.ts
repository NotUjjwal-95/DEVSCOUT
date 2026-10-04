import {
  ResearchSession,
  RequirementAnalysis,
  ResearchPlan,
  ResearchQuestion,
  ResearchTask,
  Evidence,
  GitHubResearchResult,
  DecisionReport,
  ResearchStageInfo,
  ResearchEvent
} from '../types';
import { DEFAULT_STAGES } from './whiteboardMock';

export const EVENT_PIPELINE_REQUIREMENTS: RequirementAnalysis = {
  problemStatement: 'High-throughput telemetry ingestion pipeline comparing Apache Kafka and Redpanda for 50,000 events/sec with minimal DevOps overhead.',
  coreObjective: 'Compare Apache Kafka, Redpanda, and Apache Pulsar for 50,000 events/sec IoT telemetry with minimal DevOps overhead.',
  targetScale: '50k events/second peak',
  budgetTier: 'Moderate ($200-$500/month)',
  technologies: ['Redpanda', 'Kafka', 'Go', 'ClickHouse'],
  hardConstraints: [
    '50,000 events/sec peak throughput',
    'Zero message loss under node restart',
    'Small 2-person engineering team',
    'Sub-100ms end-to-end processing'
  ],
  preferences: ['Minimal JVM tuning', 'Open source', 'Prometheus metrics native'],
  technicalDomain: 'High-Throughput Distributed Streaming & Message Brokers',
  concurrencyModel: 'Seastar thread-per-core Raft replication',
  latencySla: '< 5ms broker write tail latency; < 100ms e2e',
  deploymentTarget: 'Kubernetes (K8s) or Managed Cloud Nodes',
  teamSize: '2 engineers'
};

export const EVENT_PIPELINE_TASKS: ResearchTask[] = [
  {
    id: 't-ep-1',
    questionId: 'q-ep-1',
    title: 'Thread-Per-Core vs JVM Memory Architecture',
    description: 'Compare Redpanda C++ thread-per-core model with Kafka JVM garbage collection under sustained 50k req/sec',
    sourceType: 'web',
    status: 'completed',
    searchQuery: 'Redpanda Seastar thread-per-core benchmarks vs Kafka JVM',
    itemsFoundCount: 4
  }
];

export const EVENT_PIPELINE_QUESTIONS: ResearchQuestion[] = [
  {
    id: 'q-ep-1',
    question: 'What is the operational maintenance delta between Kafka (JVM/ZooKeeper/KRaft) vs Redpanda (C++/Seastar)?',
    priority: 'high',
    sources: ['web', 'github'],
    rationale: 'Small engineering team cannot dedicate full-time personnel to JVM garbage collection and heap tuning under load spikes.',
    tasks: EVENT_PIPELINE_TASKS,
    evidenceIds: ['ev-ep-1']
  }
];

export const EVENT_PIPELINE_PLAN: ResearchPlan = {
  id: 'plan-event-pipeline-01',
  generatedAt: '2026-09-12T14:21:00Z',
  questions: EVENT_PIPELINE_QUESTIONS,
  totalTasks: 1,
  targetedSources: ['web', 'github'],
  strategySummary: 'Focus on DevOps maintenance burden, broker resource footprint on NVMe, and client library wire compatibility.'
};

export const EVENT_PIPELINE_EVIDENCE: Evidence[] = [
  {
    id: 'ev-ep-1',
    sourceType: 'web',
    title: 'Redpanda Architecture Whitepaper: Hardware Utilization without JVM',
    domain: 'redpanda.com',
    url: 'https://redpanda.com/resources/architecture-whitepaper',
    snippet: 'Redpanda executes Raft replication in C++ via the Seastar framework, bypassing the JVM memory allocator and reducing tail latency by 72% at 50k req/sec.',
    fullQuote: 'By eliminating garbage collection pauses and using direct I/O to NVMe storage, tail latency remains sub-5ms under continuous ingestion without requiring ZooKeeper or JVM tuning.',
    relatedQuestionId: 'q-ep-1',
    relevance: 'primary',
    verified: true,
    timestamp: '2026-09-12T14:24:10Z',
    metadata: {
      citationIndex: 1,
      section: 'Architecture Assessment'
    }
  }
];

export const EVENT_PIPELINE_REPOSITORIES: GitHubResearchResult[] = [
  {
    id: 'repo-ep-1',
    owner: 'redpanda-data',
    repo: 'redpanda',
    fullName: 'redpanda-data/redpanda',
    description: 'Simple, powerful, and cost-efficient streaming data platform compatible with Apache Kafka APIs.',
    language: 'C++',
    stars: 10400,
    forks: 780,
    openIssues: 540,
    lastUpdated: '2026-09-10',
    url: 'https://github.com/redpanda-data/redpanda',
    license: 'BSL 1.1 / Apache-2.0',
    commitFrequency: 'Very Active',
    recentRelease: 'v24.2.1',
    relevanceToArchitecture: 'Drop-in Kafka alternative requiring zero JVM management and native Raft metadata.'
  }
];

export const EVENT_PIPELINE_REPORT: DecisionReport = {
  id: 'rep-event-pipeline-01',
  sessionId: 'res-event-pipeline-02',
  generatedAt: '2026-09-12T14:40:00Z',
  executiveSummary: 'For a 2-person team ingesting 50,000 IoT events/sec, Redpanda is strongly recommended over standard Apache Kafka. Redpanda provides 100% Kafka wire compatibility with zero JVM memory tuning, native Raft consensus without separate controller clusters, and 3x lower operational maintenance overhead.',
  recommendedApproach: {
    title: 'Redpanda Dedicated Cluster with Go Consumer Groups',
    fitLevel: 'high',
    architectureSummary: 'A 3-node Redpanda cluster handles event streaming with Raft consensus. Go worker pools read partitions using franz-go and batch-insert into ClickHouse columnar storage.',
    whyItFits: [
      {
        point: 'Zero JVM tuning saves ~15 hours of DevOps maintenance per month for a 2-person team.',
        evidenceIds: ['ev-ep-1']
      },
      {
        point: 'Native Raft consensus avoids running separate ZooKeeper or complicated KRaft quorum metadata nodes.',
        evidenceIds: ['ev-ep-1']
      }
    ]
  },
  alternatives: [
    {
      title: 'Apache Kafka with KRaft',
      fitLevel: 'medium',
      summary: 'The battle-tested industry standard for event streaming.',
      pros: ['Huge community and infinite ecosystem connectors', 'Vast documentation'],
      cons: ['Requires JVM heap tuning and GC pause troubleshooting', 'Higher base memory footprint on small nodes'],
      verdict: 'Viable but increases operational maintenance burden for small teams.',
      evidenceIds: ['ev-ep-1']
    }
  ],
  tradeoffs: [
    {
      dimension: 'Operational Simplicity vs Ecosystem Maturity',
      analysis: 'Redpanda provides simpler operations and lower latency, while Apache Kafka has a broader plugin library. Since standard Kafka Go clients work natively with Redpanda, ecosystem risk is minimal.',
      winner: 'Redpanda',
      evidenceIds: ['ev-ep-1']
    }
  ],
  technicalConsiderations: [
    {
      category: 'Consumer Batching',
      guidance: 'Buffer events in Go workers into 10,000-row microbatches before flushing to ClickHouse to maximize columnar compression.',
      actionableRule: 'Flush batches on whichever happens first: 5,000 events or 500 milliseconds.'
    }
  ],
  sourcesSummary: {
    webCount: 3,
    githubCount: 2,
    ragCount: 1,
    primaryDocs: ['Redpanda Technical Architecture Guide', 'Apache Kafka KRaft Specification']
  }
};

export const EVENT_PIPELINE_SESSION: ResearchSession = {
  id: 'res-event-pipeline-02',
  projectName: 'High-Throughput Event Ingestion',
  objective: 'Compare Apache Kafka, Redpanda, and Apache Pulsar for 50,000 events/sec IoT telemetry with minimal DevOps overhead.',
  state: 'completed',
  status: 'completed',
  currentStage: 'decision_analysis',
  currentStageIndex: 7,
  createdAt: '2026-09-12T14:20:00Z',
  updatedAt: '2026-09-12T14:45:00Z',
  requirementAnalysis: EVENT_PIPELINE_REQUIREMENTS,
  plan: EVENT_PIPELINE_PLAN,
  stages: DEFAULT_STAGES,
  events: [
    { id: 'ep-e1', timestamp: '14:20:10', stageId: 'requirement_analysis', type: 'info', message: 'Analyzed throughput ceiling: 50,000 events/sec with strict durability' },
    { id: 'ep-e2', timestamp: '14:22:00', stageId: 'github_research', type: 'artifact', message: 'Audited Redpanda C++ thread-per-core storage engine architecture' },
    { id: 'ep-e3', timestamp: '14:25:30', stageId: 'decision_analysis', type: 'success', message: 'Decision reached: Redpanda selected over Apache Kafka due to zero JVM overhead and native Raft' }
  ],
  activityEvents: [
    { id: 'ep-e1', timestamp: '14:20:10', stageId: 'requirement_analysis', type: 'info', message: 'Analyzed throughput ceiling: 50,000 events/sec with strict durability' },
    { id: 'ep-e2', timestamp: '14:22:00', stageId: 'github_research', type: 'artifact', message: 'Audited Redpanda C++ thread-per-core storage engine architecture' },
    { id: 'ep-e3', timestamp: '14:25:30', stageId: 'decision_analysis', type: 'success', message: 'Decision reached: Redpanda selected over Apache Kafka due to zero JVM overhead and native Raft' }
  ],
  evidence: EVENT_PIPELINE_EVIDENCE,
  repositories: EVENT_PIPELINE_REPOSITORIES,
  githubRepos: EVENT_PIPELINE_REPOSITORIES,
  questions: EVENT_PIPELINE_QUESTIONS,
  scale: EVENT_PIPELINE_REQUIREMENTS.targetScale,
  budget: EVENT_PIPELINE_REQUIREMENTS.budgetTier,
  technologies: EVENT_PIPELINE_REQUIREMENTS.technologies,
  constraints: EVENT_PIPELINE_REQUIREMENTS.hardConstraints,
  preferences: EVENT_PIPELINE_REQUIREMENTS.preferences,
  report: EVENT_PIPELINE_REPORT
};
