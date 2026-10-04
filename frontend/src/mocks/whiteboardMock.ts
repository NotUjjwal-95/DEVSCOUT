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

export const DEFAULT_STAGES: ResearchStageInfo[] = [
  {
    id: 'requirement_analysis',
    name: 'Requirement Analysis',
    description: 'Decompose constraints, concurrency targets, and state models',
    status: 'completed',
    durationSeconds: 2
  },
  {
    id: 'research_planning',
    name: 'Research Planning',
    description: 'Formulate architectural questions and evidence criteria',
    status: 'completed',
    durationSeconds: 3
  },
  {
    id: 'task_generation',
    name: 'Task Generation',
    description: 'Spin up source-directed probes for Web, GitHub, and RAG',
    status: 'completed',
    durationSeconds: 2
  },
  {
    id: 'web_research',
    name: 'Web Research',
    description: 'Crawl official technical documentation, RFCs, and peer benchmarks',
    status: 'completed',
    durationSeconds: 4
  },
  {
    id: 'github_research',
    name: 'GitHub Research',
    description: 'Audit production repositories, library activity, and open issues',
    status: 'completed',
    durationSeconds: 4
  },
  {
    id: 'rag_research',
    name: 'RAG Research',
    description: 'Query DEVSCOUT curated engineering knowledge corpus',
    status: 'completed',
    durationSeconds: 3
  },
  {
    id: 'evidence_processing',
    name: 'Evidence Processing',
    description: 'Normalize snippets, verify peer-reviewed claims, deduplicate',
    status: 'completed',
    durationSeconds: 3
  },
  {
    id: 'decision_analysis',
    name: 'Decision Analysis',
    description: 'Synthesize trade-off matrix, fit criteria, and recommendation',
    status: 'completed',
    durationSeconds: 3
  }
];

export const WHITEBOARD_REQUIREMENT_ANALYSIS: RequirementAnalysis = {
  problemStatement: 'Multi-user real-time whiteboard canvas with stylus vector drawing, cursor presence, and room state persistence.',
  coreObjective: 'Build a real-time collaborative whiteboard using React and Go supporting concurrent drawing, multi-cursor presence, and persistent room state.',
  targetScale: '~1,000 concurrent users',
  budgetTier: 'Low / Bootstrapped ($20-$50/month)',
  technologies: ['React', 'Go', 'WebSockets', 'CRDT', 'PostgreSQL'],
  hardConstraints: [
    'Sub-30ms local drawing latency',
    '~1,000 concurrent active users',
    'Open source runtime stack',
    'Low operational infrastructure budget'
  ],
  preferences: ['Open source', 'Self-hosted', 'Minimal operational overhead'],
  technicalDomain: 'Distributed Real-Time Systems & Collaborative Vector Graphics',
  concurrencyModel: 'Goroutine-per-connection fanout hub with buffered non-blocking channels',
  latencySla: '< 30ms local stylus rendering; < 50ms peer propagation',
  deploymentTarget: 'Docker container on single Hetzner Cloud VM ($20/mo)',
  teamSize: '3 full-stack engineers',
  existingStack: 'React 19, TypeScript, Go 1.24, PostgreSQL 16'
};

export const WHITEBOARD_TASKS: ResearchTask[] = [
  {
    id: 't-1-1',
    questionId: 'q-1',
    title: 'Canvas Synchronization Paradigm Analysis',
    description: 'Analyze CRDT vs OT algorithms for 2D spatial canvas environments',
    sourceType: 'rag',
    status: 'completed',
    searchQuery: 'CRDT vs OT canvas conflict resolution',
    itemsFoundCount: 3
  },
  {
    id: 't-1-2',
    questionId: 'q-1',
    title: 'Yjs Vector Storage & Wire Format Benchmark',
    description: 'Evaluate Yjs memory footprint and wire serialization format',
    sourceType: 'web',
    status: 'completed',
    searchQuery: 'Yjs benchmark canvas operations',
    itemsFoundCount: 4
  },
  {
    id: 't-1-3',
    questionId: 'q-1',
    title: 'Automerge v2 Performance Audit',
    description: 'Investigate Automerge v2 binary format performance on stroke sequences',
    sourceType: 'web',
    status: 'completed',
    searchQuery: 'Automerge v2 vector synchronization performance',
    itemsFoundCount: 2
  },
  {
    id: 't-2-1',
    questionId: 'q-2',
    title: 'Go WebSocket Hub Concurrency Audit',
    description: 'Audit gorilla/websocket vs nhooyr/websocket for memory efficiency on Linux epoll',
    sourceType: 'github',
    status: 'completed',
    searchQuery: 'Go websocket library memory benchmarks',
    itemsFoundCount: 4
  },
  {
    id: 't-2-2',
    questionId: 'q-2',
    title: 'Go Room Fan-Out Channel Pattern',
    description: 'Profile room fan-out broadcast pattern with buffered channels',
    sourceType: 'rag',
    status: 'completed',
    searchQuery: 'Go websocket hub room isolation patterns',
    itemsFoundCount: 2
  },
  {
    id: 't-2-3',
    questionId: 'q-2',
    title: 'RFC 6455 Frame Framing Overhead',
    description: 'Verify RFC 6455 frame overhead compared to SSE + HTTP POST',
    sourceType: 'web',
    status: 'completed',
    searchQuery: 'RFC 6455 frame latency vs HTTP POST',
    itemsFoundCount: 3
  },
  {
    id: 't-3-1',
    questionId: 'q-3',
    title: 'y-websocket Awareness Protocol Inspection',
    description: 'Examine y-websocket awareness protocol wire format and presence timeout',
    sourceType: 'github',
    status: 'completed',
    searchQuery: 'y-websocket awareness protocol implementation',
    itemsFoundCount: 3
  },
  {
    id: 't-4-1',
    questionId: 'q-4',
    title: 'tldraw Canvas Document Lifecycle Audit',
    description: 'Inspect tldraw canvas document record lifecycle and CRDT store bindings',
    sourceType: 'github',
    status: 'completed',
    searchQuery: 'tldraw persistence bindings',
    itemsFoundCount: 5
  },
  {
    id: 't-4-2',
    questionId: 'q-4',
    title: 'PostgreSQL BYTEA Snapshot Compaction',
    description: 'Test PostgreSQL BYTEA chunk compression with zstandard for document recovery',
    sourceType: 'web',
    status: 'completed',
    searchQuery: 'PostgreSQL binary delta snapshotting',
    itemsFoundCount: 2
  }
];

export const WHITEBOARD_QUESTIONS: ResearchQuestion[] = [
  {
    id: 'q-1',
    question: 'How should real-time state synchronization and conflict resolution be implemented?',
    priority: 'high',
    sources: ['web', 'github', 'rag'],
    rationale: 'Synchronization strategy directly determines multi-user cursor latency, offline resilience, and server compute overhead under concurrent drawing strokes.',
    tasks: WHITEBOARD_TASKS.filter(t => t.questionId === 'q-1'),
    evidenceIds: ['ev-1', 'ev-3', 'ev-4']
  },
  {
    id: 'q-2',
    question: 'What network transport and Go concurrency model best scales to 1,000 concurrent rooms?',
    priority: 'high',
    sources: ['web', 'github', 'rag'],
    rationale: 'Go websocket hub architecture must isolate room broadcast queues without head-of-line blocking or excessive goroutine leak.',
    tasks: WHITEBOARD_TASKS.filter(t => t.questionId === 'q-2'),
    evidenceIds: ['ev-2', 'ev-6', 'ev-8']
  },
  {
    id: 'q-3',
    question: 'How should ephemeral cursor positions and presence be separated from canvas state?',
    priority: 'medium',
    sources: ['github', 'rag'],
    rationale: 'Streaming cursor coordinates at 60Hz into the persistent document log causes document explosion and unnecessary disk I/O.',
    tasks: WHITEBOARD_TASKS.filter(t => t.questionId === 'q-3'),
    evidenceIds: ['ev-5']
  },
  {
    id: 'q-4',
    question: 'What persistence and snapshot compaction strategy fits PostgreSQL?',
    priority: 'medium',
    sources: ['web', 'github'],
    rationale: 'Replaying 50,000 historical drawing deltas on initial room join causes noticeable UI freeze without binary snapshot compaction.',
    tasks: WHITEBOARD_TASKS.filter(t => t.questionId === 'q-4'),
    evidenceIds: ['ev-7', 'ev-9']
  }
];

export const WHITEBOARD_PLAN: ResearchPlan = {
  id: 'plan-whiteboard-01',
  generatedAt: '2026-09-18T10:13:00Z',
  questions: WHITEBOARD_QUESTIONS,
  totalTasks: WHITEBOARD_TASKS.length,
  targetedSources: ['web', 'github', 'rag'],
  strategySummary: 'Prioritize conflict resolution architecture first (CRDT vs OT), evaluate transport layer memory limits in Go, and isolate volatile presence updates from durable storage.'
};

export const WHITEBOARD_EVIDENCE: Evidence[] = [
  {
    id: 'ev-1',
    sourceType: 'web',
    title: 'Yjs Architecture & Conflict-Free Replicated Data Types',
    domain: 'docs.yjs.dev',
    url: 'https://docs.yjs.dev/getting-started/how-it-works',
    snippet: 'Yjs uses a state-vector based differential synchronization protocol. Binary updates are compact (<100 bytes per drawing stroke) and merge idempotently without central server locks.',
    fullQuote: 'Yjs represents shared data as a sequence of operations with Lamport timestamps and client IDs. Updates can be batched and transmitted over raw WebSockets or WebRTC without requiring the server to evaluate conflict logic. This ensures deterministic convergence on all clients even with out-of-order packet arrival.',
    relatedQuestionId: 'q-1',
    relevance: 'primary',
    verified: true,
    timestamp: '2026-09-18T10:14:22Z',
    webDetails: {
      id: 'web-1',
      title: 'Yjs Architecture Specification',
      domain: 'docs.yjs.dev',
      url: 'https://docs.yjs.dev/getting-started/how-it-works',
      snippet: 'State-vector synchronization mechanism',
      section: 'Internal Data Representation',
      citationIndex: 1,
      confidenceScore: 0.98
    },
    metadata: {
      citationIndex: 1,
      section: 'Internal Data Representation'
    }
  },
  {
    id: 'ev-2',
    sourceType: 'github',
    title: 'gorilla/websocket — Go WebSocket implementation',
    domain: 'github.com',
    url: 'https://github.com/gorilla/websocket',
    snippet: 'Production-tested Go WebSocket implementation. Zero-copy buffer pooling handles 10,000+ idle client connections per GB of RAM on Linux epoll.',
    fullQuote: 'gorilla/websocket provides a complete, tested implementation of RFC 6455. Benchmarked against raw TCP socket layers, its read/write buffer reuse pattern minimizes garbage collection pauses under high concurrency.',
    relatedQuestionId: 'q-2',
    relevance: 'primary',
    verified: true,
    timestamp: '2026-09-18T10:16:45Z',
    githubDetails: {
      id: 'gh-1',
      owner: 'gorilla',
      repo: 'websocket',
      fullName: 'gorilla/websocket',
      description: 'A fast, well-tested and widely used WebSocket implementation for Go.',
      language: 'Go',
      stars: 22840,
      forks: 3410,
      openIssues: 42,
      lastUpdated: '2026-08-30',
      url: 'https://github.com/gorilla/websocket',
      license: 'BSD-2-Clause',
      commitFrequency: 'Stable / Maintenance mode',
      recentRelease: 'v1.5.3',
      relevanceToArchitecture: 'Benchmark baseline for Go WebSocket servers. Handles client read/write pumps with zero-copy buffer pooling.'
    },
    metadata: {
      repoLanguage: 'Go',
      repoStars: 22840,
      lastCommit: '2026-08-30'
    }
  },
  {
    id: 'ev-3',
    sourceType: 'web',
    title: 'Automerge vs Yjs Benchmark Suite',
    domain: 'josephg.com',
    url: 'https://josephg.com/blog/crdt-benchmarks-2024',
    snippet: 'In canvas and graphical vector sync tests, Yjs exhibited 4.2x faster initial document parse times and 60% lower memory overhead than Automerge v2 due to flat item-array storage.',
    fullQuote: 'When testing continuous vector paths containing 5,000 coordinate deltas, Yjs memory consumption plateaued at 14MB client memory compared to 38MB in Automerge. Garbage collection of deleted stroke tombstones remains necessary in long-lived whiteboard rooms.',
    relatedQuestionId: 'q-1',
    relevance: 'benchmark',
    verified: true,
    timestamp: '2026-09-18T10:18:11Z',
    metadata: {
      citationIndex: 2,
      section: 'Memory Profiling & Serialization'
    }
  },
  {
    id: 'ev-4',
    sourceType: 'rag',
    title: 'DEVSCOUT KB: Operational Transformation vs CRDT in Multi-Cursor Canvas',
    domain: 'devscout.internal/dist-systems',
    url: 'internal://knowledge-base/dist-systems/ot-vs-crdt-canvas',
    snippet: 'OT mandates an authoritative central server holding linear transformation histories. For visual whiteboards where freehand strokes produce 60 updates/sec, OT introduces server serialization bottlenecks.',
    fullQuote: 'Operational Transformation requires the server to transform every incoming delta against all concurrent pending deltas before broadcasting. For text documents this works well, but for canvas coordinates with multi-user stroke streaming, OT creates head-of-line blocking on the central server process.',
    relatedQuestionId: 'q-1',
    relevance: 'high',
    verified: true,
    timestamp: '2026-09-18T10:20:00Z',
    metadata: {
      author: 'Distributed Systems Practice Group',
      section: 'Architecture Assessment'
    }
  },
  {
    id: 'ev-5',
    sourceType: 'github',
    title: 'y-websocket — WebSocket provider for Yjs',
    domain: 'github.com',
    url: 'https://github.com/yjs/y-websocket',
    snippet: 'Reference WebSocket client and Node.js server. Exposes room-based awareness protocol for ephemeral pointer locations and user presence without polluting CRDT document history.',
    fullQuote: 'The awareness protocol runs on top of the WebSocket connection but stores cursor positions in volatile in-memory maps. Ephemeral presence is decoupled from persistent document state, avoiding document size bloat from mouse movement events.',
    relatedQuestionId: 'q-3',
    relevance: 'primary',
    verified: true,
    timestamp: '2026-09-18T10:21:40Z',
    metadata: {
      repoLanguage: 'JavaScript',
      repoStars: 1850,
      lastCommit: '2026-09-02'
    }
  },
  {
    id: 'ev-6',
    sourceType: 'web',
    title: 'RFC 6455: The WebSocket Protocol Standard',
    domain: 'rfc-editor.org',
    url: 'https://datatracker.ietf.org/doc/html/rfc6455',
    snippet: 'Full-duplex bidirectional frame transport over a single TCP connection. Provides sub-millisecond client-to-server messaging without HTTP request-header overhead.',
    fullQuote: 'WebSocket reduces per-message overhead from ~800 bytes (HTTP/1.1 headers) to 2 to 10 bytes framing. Essential for high-cadence coordinate streaming where round-trip latency must remain under 30ms for seamless stylus drawing.',
    relatedQuestionId: 'q-2',
    relevance: 'primary',
    verified: true,
    timestamp: '2026-09-18T10:22:15Z',
    metadata: {
      citationIndex: 3,
      section: 'Protocol Overview'
    }
  },
  {
    id: 'ev-7',
    sourceType: 'github',
    title: 'tldraw/tldraw — Open Source Collaborative Canvas',
    domain: 'github.com',
    url: 'https://github.com/tldraw/tldraw',
    snippet: 'Production React canvas engine designed for collaborative whiteboarding. Uses incremental spatial indexing (R-tree) and separate ephemeral presence layers.',
    fullQuote: 'tldraw separates document records (shapes, bindings) from transient session state (camera, pointers, selection boxes). Allows direct binding to Yjs or custom CRDT stores with minimal re-render surface.',
    relatedQuestionId: 'q-4',
    relevance: 'high',
    verified: true,
    timestamp: '2026-09-18T10:24:02Z',
    metadata: {
      repoLanguage: 'TypeScript',
      repoStars: 38400,
      lastCommit: '2026-09-15'
    }
  },
  {
    id: 'ev-8',
    sourceType: 'rag',
    title: 'DEVSCOUT KB: Go Concurrency Patterns for Real-Time Fan-Out Hubs',
    domain: 'devscout.internal/go-patterns',
    url: 'internal://knowledge-base/go/websocket-fanout-hub',
    snippet: 'A dedicated Hub goroutine managing client registration and broadcast channels prevents lock contention. Buffered client egress channels prevent slow network peers from stalling the room.',
    fullQuote: 'Under Go runtime schedulers, each WebSocket connection uses two goroutines: readPump and writePump. A non-blocking select on the client send channel with a 256-message buffer drops lagged ephemeral frames rather than blocking the hub broadcast loop.',
    relatedQuestionId: 'q-2',
    relevance: 'high',
    verified: true,
    timestamp: '2026-09-18T10:26:30Z',
    metadata: {
      author: 'High Concurrency Infrastructure Team'
    }
  },
  {
    id: 'ev-9',
    sourceType: 'web',
    title: 'PostgreSQL BYTEA Storage for CRDT Compaction',
    domain: 'postgresql.org',
    url: 'https://www.postgresql.org/docs/current/datatype-binary.html',
    snippet: 'Periodic state compaction stores compressed Yjs binary blobs into PostgreSQL BYTEA columns, keeping cold document load time under 80ms while retaining room audit trail.',
    fullQuote: 'Rather than storing every single stroke delta permanently in relational rows, snapshotting document states every 5 minutes or upon idle periods collapses thousands of operation vectors into a compact 120KB binary chunk.',
    relatedQuestionId: 'q-4',
    relevance: 'medium',
    verified: true,
    timestamp: '2026-09-18T10:28:10Z',
    metadata: {
      citationIndex: 4
    }
  }
];

export const WHITEBOARD_REPOSITORIES: GitHubResearchResult[] = [
  {
    id: 'repo-1',
    owner: 'gorilla',
    repo: 'websocket',
    fullName: 'gorilla/websocket',
    description: 'Fast, well-tested and widely used WebSocket implementation for Go. RFC 6455 compliant.',
    language: 'Go',
    stars: 22840,
    forks: 3410,
    openIssues: 42,
    lastUpdated: '2026-08-30',
    url: 'https://github.com/gorilla/websocket',
    license: 'BSD-2-Clause',
    commitFrequency: 'Stable / Maintenance mode',
    recentRelease: 'v1.5.3 (Active patch cadence)',
    relevanceToArchitecture: 'Benchmark baseline for Go WebSocket servers. Handles client read/write pumps with zero-copy buffer pooling.'
  },
  {
    id: 'repo-2',
    owner: 'yjs',
    repo: 'yjs',
    fullName: 'yjs/yjs',
    description: 'Shared data types for building collaborative software. State-vector differential sync engine.',
    language: 'JavaScript',
    stars: 17200,
    forks: 1190,
    openIssues: 98,
    lastUpdated: '2026-09-14',
    url: 'https://github.com/yjs/yjs',
    license: 'MIT',
    commitFrequency: 'Very Active (>15 commits/month)',
    recentRelease: 'v13.6.14',
    relevanceToArchitecture: 'Leading CRDT implementation for web browsers. Direct integration with React, ProseMirror, Monaco, and canvas.'
  },
  {
    id: 'repo-3',
    owner: 'tldraw',
    repo: 'tldraw',
    fullName: 'tldraw/tldraw',
    description: 'A very good whiteboard. Fast React canvas SDK and multiplayer drawing engine.',
    language: 'TypeScript',
    stars: 38400,
    forks: 2450,
    openIssues: 184,
    lastUpdated: '2026-09-15',
    url: 'https://github.com/tldraw/tldraw',
    license: 'Apache-2.0',
    commitFrequency: 'Extremely Active (>40 commits/month)',
    recentRelease: 'v2.4.2',
    relevanceToArchitecture: 'State-of-the-art canvas primitives, spatial indexing, brush smoothing, and pluggable sync store.'
  },
  {
    id: 'repo-4',
    owner: 'yjs',
    repo: 'y-websocket',
    fullName: 'yjs/y-websocket',
    description: 'WebSocket provider for Yjs with room awareness, persistence hooks, and reconnection handling.',
    language: 'JavaScript',
    stars: 1850,
    forks: 410,
    openIssues: 34,
    lastUpdated: '2026-09-02',
    url: 'https://github.com/yjs/y-websocket',
    license: 'MIT',
    commitFrequency: 'Active',
    recentRelease: 'v1.5.4',
    relevanceToArchitecture: 'Defines the binary awareness wire standard for ephemeral pointer coordinates and connection lifecycle.'
  }
];

export const WHITEBOARD_REPORT: DecisionReport = {
  id: 'rep-whiteboard-01',
  sessionId: 'res-whiteboard-01',
  generatedAt: '2026-09-18T10:30:00Z',
  executiveSummary: 'For a real-time collaborative whiteboard built with React and Go targeting ~1,000 concurrent users with low operational budget, the optimal architecture pairs a React canvas front-end with Conflict-Free Replicated Data Types (Yjs) running over bidirectional WebSockets connected to a Go room-multiplexing hub. This avoids central operational transformation locks, keeps server memory footprint under 250MB across 1,000 concurrent rooms, and provides sub-20ms local feedback.',
  recommendedApproach: {
    title: 'WebSockets + CRDT (Yjs via y-websocket with Go Hub Bridge)',
    fitLevel: 'high',
    architectureSummary: 'Clients edit canvas primitives into a local Yjs document instance, providing zero-latency local optimistic rendering. Stroke deltas are serialized as compact binary updates and dispatched over persistent WebSockets. A Go backend acts as a room-isolated fan-out message router and periodic snapshot aggregator into PostgreSQL BYTEA storage, eliminating server-side conflict resolution bottlenecks.',
    whyItFits: [
      {
        point: 'Client-side CRDT evaluation completely eliminates expensive operational transform calculations on the Go server, allowing a single modest $20/mo VM to support 1,000+ active rooms.',
        evidenceIds: ['ev-1', 'ev-4']
      },
      {
        point: 'Sub-20ms drawing responsiveness: user strokes render locally without awaiting round-trip server confirmation, with deterministic conflict-free merging on remote peers.',
        evidenceIds: ['ev-1', 'ev-3']
      },
      {
        point: 'RFC 6455 WebSockets provide full-duplex binary frame streaming with minimal 2–4 byte framing overhead compared to heavy HTTP polling.',
        evidenceIds: ['ev-6', 'ev-2']
      },
      {
        point: 'Go goroutine-per-client model combined with buffered non-blocking broadcast channels guarantees that one slow mobile client never blocks room broadcasts for others.',
        evidenceIds: ['ev-2', 'ev-8']
      },
      {
        point: 'Separation of ephemeral cursor awareness from permanent shape mutations prevents document history explosion from high-frequency mouse movements.',
        evidenceIds: ['ev-5', 'ev-7']
      }
    ]
  },
  alternatives: [
    {
      title: 'Conflict-Free Replicated Data Types (CRDT)',
      fitLevel: 'high',
      summary: 'State-vector based differential replication. Merges concurrent edits deterministically across peers without central coordinator.',
      pros: [
        'Zero-latency local optimistic UI updates',
        'Works offline and seamlessly reconciles upon reconnection',
        'Minimal server compute burden: server only routes binary deltas'
      ],
      cons: [
        'Requires periodic document compaction to prevent tombstone growth',
        'Learning curve for custom collaborative data structures'
      ],
      verdict: 'Recommended primary synchronization paradigm for vector canvas applications.',
      evidenceIds: ['ev-1', 'ev-3', 'ev-4']
    },
    {
      title: 'Operational Transformation (OT)',
      fitLevel: 'medium',
      summary: 'Centralized algorithm requiring an authoritative server to transform operations against all concurrent inflight transactions.',
      pros: [
        'Standard in rich-text editors (e.g., Google Docs, ShareDB)',
        'Compact document history without tombstones'
      ],
      cons: [
        'Heavy server compute overhead when handling 60fps freehand drawing coordinate streams',
        'Requires strict total ordering, resulting in head-of-line blocking under packet loss',
        'High operational complexity to scale server infrastructure'
      ],
      verdict: 'Suboptimal for coordinate-heavy visual whiteboards due to high server serialization cost.',
      evidenceIds: ['ev-4']
    },
    {
      title: 'Raw WebSocket Coordinate Fan-Out (Transport Layer Only)',
      fitLevel: 'low',
      summary: 'Sending raw x,y coordinate JSON packets to server and broadcasting to all room members without a formal sync engine.',
      pros: [
        'Trivial to implement in first 2 hours',
        'Zero library dependencies'
      ],
      cons: [
        'No conflict resolution: simultaneous modifications overwrite or desync',
        'No offline support or disconnect recovery',
        'Requires custom ad-hoc state reconciliation logic that degrades quickly'
      ],
      verdict: 'Acceptable only for throwaway prototypes; unacceptable for production multi-user drawing.',
      evidenceIds: ['ev-1', 'ev-6']
    }
  ],
  tradeoffs: [
    {
      dimension: 'Client Memory vs Server Compute Burden',
      analysis: 'CRDT shifts conflict resolution calculation to the client runtime. Yjs keeps client memory footprint around 14MB for typical whiteboards while reducing server CPU utilization by over 85% compared to OT.',
      winner: 'CRDT (Yjs)',
      evidenceIds: ['ev-3', 'ev-4']
    },
    {
      dimension: 'Document Size Growth vs History Replay',
      analysis: 'Deleted canvas shapes leave invisible CRDT tombstones to maintain causal order. Without snapshot compaction, long sessions grow in memory. Mitigated by periodic PostgreSQL snapshotting.',
      winner: 'Mitigated with Snapshot Compaction',
      evidenceIds: ['ev-3', 'ev-9']
    },
    {
      dimension: 'Ephemeral Presence Overhead vs Precision',
      analysis: 'Broadcasting mouse cursor updates at 60Hz across 50 users in a room creates 3,000 msgs/sec. Decoupling ephemeral presence with throttle/deadband logic reduces network packets by 70%.',
      winner: 'Decoupled Awareness Protocol',
      evidenceIds: ['ev-5']
    }
  ],
  technicalConsiderations: [
    {
      category: 'Client Canvas Performance',
      guidance: 'Do not re-render the entire canvas on every remote stroke update. Use an incremental dirty-rect bounding box or spatial index (e.g. tldraw engine).',
      actionableRule: 'Isolate transient cursor overlays onto a separate transparent HTML canvas or SVG layer above the main shape layer.'
    },
    {
      category: 'Network Reconnection & Resiliency',
      guidance: 'WebSocket drops are frequent on mobile and Wi-Fi networks. The synchronization layer must resume state using Yjs state vectors rather than full room reloads.',
      actionableRule: 'Implement exponential backoff with jitter on WebSocket reconnects; exchange state vectors upon handshake.'
    },
    {
      category: 'Storage & Database Snapshotting',
      guidance: 'Do not store individual cursor deltas in relational rows. Periodically serialize the consolidated Yjs document state as a binary blob into PostgreSQL.',
      actionableRule: 'Compact and write document snapshot to PostgreSQL BYTEA column every 100 operations or upon 60 seconds of room inactivity.'
    },
    {
      category: 'Go Concurrency Guardrails',
      guidance: 'Slow network connections on client devices can back up Go write channels and stall the room hub goroutine if unbuffered.',
      actionableRule: 'Enforce non-blocking sends with client-side buffer limit (256 frames). Drop dropped awareness frames and disconnect persistently lagged clients.'
    }
  ],
  sourcesSummary: {
    webCount: 4,
    githubCount: 4,
    ragCount: 2,
    primaryDocs: ['RFC 6455', 'Yjs Architecture Specification', 'gorilla/websocket Reference', 'tldraw Architecture Guide']
  }
};

export const WHITEBOARD_EVENTS: ResearchEvent[] = [
  { id: 'ev-l-1', timestamp: '10:12:05', stageId: 'requirement_analysis', type: 'info', message: 'Parsed user objective: Real-time collaborative whiteboard (React + Go)' },
  { id: 'ev-l-2', timestamp: '10:12:18', stageId: 'requirement_analysis', type: 'info', message: 'Extracted 4 technical constraints: latency < 30ms, ~1,000 concurrent users, open source, low budget' },
  { id: 'ev-l-3', timestamp: '10:13:02', stageId: 'research_planning', type: 'info', message: 'Formulated 4 core architectural research questions across synchronization, network transport, presence, and persistence' },
  { id: 'ev-l-4', timestamp: '10:14:15', stageId: 'task_generation', type: 'info', message: 'Dispatched 9 targeted research probes across Web, GitHub, and RAG knowledge bases' },
  { id: 'ev-l-5', timestamp: '10:15:30', stageId: 'web_research', type: 'artifact', message: 'Extracted benchmark data: Yjs vs Automerge v2 memory footprint on canvas coordinate streams' },
  { id: 'ev-l-6', timestamp: '10:16:48', stageId: 'github_research', type: 'artifact', message: 'Audited gorilla/websocket, tldraw, yjs, and y-websocket for production readiness' },
  { id: 'ev-l-7', timestamp: '10:18:20', stageId: 'rag_research', type: 'info', message: 'Retrieved distributed systems trade-off analysis: OT vs CRDT under high-frequency vector drawing' },
  { id: 'ev-l-8', timestamp: '10:20:10', stageId: 'evidence_processing', type: 'success', message: 'Consolidated 9 high-relevance evidence items and verified primary citations against RFC 6455' },
  { id: 'ev-l-9', timestamp: '10:21:45', stageId: 'decision_analysis', type: 'success', message: 'Generated Decision Report: WebSockets + CRDT (Yjs) with Go Hub Bridge' }
];

export const CANONICAL_WHITEBOARD_SESSION: ResearchSession = {
  id: 'res-whiteboard-01',
  projectName: 'Real-Time Collaborative Whiteboard',
  objective: 'Build a real-time collaborative whiteboard using React and Go supporting concurrent drawing, multi-cursor presence, and persistent room state.',
  state: 'completed',
  status: 'completed',
  currentStage: 'decision_analysis',
  currentStageIndex: 7,
  createdAt: '2026-09-18T10:12:00Z',
  updatedAt: '2026-09-18T10:32:00Z',
  requirementAnalysis: WHITEBOARD_REQUIREMENT_ANALYSIS,
  plan: WHITEBOARD_PLAN,
  stages: DEFAULT_STAGES,
  events: WHITEBOARD_EVENTS,
  activityEvents: WHITEBOARD_EVENTS,
  evidence: WHITEBOARD_EVIDENCE,
  repositories: WHITEBOARD_REPOSITORIES,
  githubRepos: WHITEBOARD_REPOSITORIES,
  questions: WHITEBOARD_QUESTIONS,
  scale: WHITEBOARD_REQUIREMENT_ANALYSIS.targetScale,
  budget: WHITEBOARD_REQUIREMENT_ANALYSIS.budgetTier,
  technologies: WHITEBOARD_REQUIREMENT_ANALYSIS.technologies,
  constraints: WHITEBOARD_REQUIREMENT_ANALYSIS.hardConstraints,
  preferences: WHITEBOARD_REQUIREMENT_ANALYSIS.preferences,
  report: WHITEBOARD_REPORT
};
