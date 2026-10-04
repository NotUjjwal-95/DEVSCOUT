import React, { useState } from 'react';
import { ResearchObjectiveInput } from '../../types/research';
import {
  Compass,
  ArrowRight,
  Plus,
  X,
  Sliders,
  Sparkles,
  Zap,
  Layers,
  Server,
  DollarSign,
  Shield,
  Clock,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface NewResearchViewProps {
  onStart: (input: ResearchObjectiveInput) => void;
  isStarting?: boolean;
}

interface PresetTemplate {
  name: string;
  tagline: string;
  objective: string;
  technologies: string[];
  constraints: string[];
  scale: string;
  budget: string;
  preferences: string[];
  advanced: {
    deploymentTarget: string;
    latencyTarget: string;
    teamSize: string;
    existingStack: string;
  };
}

const PRESET_TEMPLATES: PresetTemplate[] = [
  {
    name: 'Real-Time Whiteboard',
    tagline: 'React + Go multiplayer canvas with CRDT & WebSockets',
    objective: 'Build a real-time collaborative whiteboard using React and Go supporting concurrent freehand drawing, multi-cursor presence, and persistent room state.',
    technologies: ['React', 'Go', 'WebSockets', 'CRDT', 'PostgreSQL'],
    constraints: ['~1,000 concurrent users', 'Low budget ($20-$50/mo)', 'Open source stack', 'Sub-30ms local latency'],
    scale: '~1,000 concurrent users',
    budget: 'Low / Bootstrapped',
    preferences: ['Open source', 'Self-hosted', 'Minimal operational overhead'],
    advanced: {
      deploymentTarget: 'Docker on Single VM',
      latencyTarget: '< 30ms local feedback',
      teamSize: '3 engineers',
      existingStack: 'React 19 + Go 1.24 + PostgreSQL 16'
    }
  },
  {
    name: '50k/sec Event Ingestion',
    tagline: 'Kafka vs Redpanda for high-throughput IoT telemetry',
    objective: 'Compare Apache Kafka, Redpanda, and Apache Pulsar for 50,000 events/sec IoT telemetry with minimal DevOps overhead.',
    technologies: ['Redpanda', 'Kafka', 'Go', 'ClickHouse'],
    constraints: ['50k events/sec', 'Zero message loss', '2-person team', 'Sub-100ms end-to-end'],
    scale: '50k events/second peak',
    budget: 'Moderate ($200-$500/mo)',
    preferences: ['Minimal JVM tuning', 'Open source', 'Prometheus metrics'],
    advanced: {
      deploymentTarget: 'Kubernetes (K8s)',
      latencyTarget: '< 100ms end-to-end',
      teamSize: '2 engineers',
      existingStack: 'Go + Docker + K8s'
    }
  },
  {
    name: 'Offline-First Mobile Sync',
    tagline: 'ElectricSQL vs PowerSync vs WatermelonDB',
    objective: 'Architect offline-first local state synchronization for a field service mobile application reconciling with PostgreSQL backend.',
    technologies: ['React Native', 'PostgreSQL', 'ElectricSQL', 'PowerSync', 'SQLite'],
    constraints: ['Intermittent connectivity', 'Bidirectional sync', 'Conflict resolution', 'Zero data loss'],
    scale: '5,000 field technicians',
    budget: 'Moderate ($150-$400/mo)',
    preferences: ['Open source', 'Batteries included', 'Row-level security'],
    advanced: {
      deploymentTarget: 'AWS ECS + Supabase/PostgreSQL',
      latencyTarget: 'Local instant (< 5ms)',
      teamSize: '4 engineers',
      existingStack: 'React Native + TypeScript + Node.js'
    }
  }
];

const TECH_SUGGESTIONS = ['React', 'Go', 'WebSockets', 'CRDT', 'Rust', 'PostgreSQL', 'Redis', 'Kafka', 'Redpanda', 'ClickHouse', 'Docker', 'GraphQL'];
const CONSTRAINT_SUGGESTIONS = ['~1,000 users', 'Sub-30ms latency', 'Zero data loss', 'Small team (2-3)', 'Low budget ($20-$50/mo)', 'GDPR compliant'];
const PREFERENCE_SUGGESTIONS = ['Open source', 'Self-hosted', 'Managed cloud', 'Minimal DevOps overhead', 'Strong TypeScript typing'];

export const NewResearchView: React.FC<NewResearchViewProps> = ({ onStart, isStarting = false }) => {
  const [objective, setObjective] = useState(
    'Build a real-time collaborative whiteboard using React and Go supporting concurrent drawing, multi-cursor presence, and persistent room state.'
  );

  const [technologies, setTechnologies] = useState<string[]>(['React', 'Go', 'WebSockets', 'CRDT']);
  const [newTechInput, setNewTechInput] = useState('');

  const [constraints, setConstraints] = useState<string[]>([
    '~1,000 concurrent users',
    'Low budget ($20-$50/mo)',
    'Sub-30ms local latency'
  ]);
  const [newConstraintInput, setNewConstraintInput] = useState('');

  const [scale, setScale] = useState('~1,000 concurrent users');
  const [budget, setBudget] = useState('Low / Bootstrapped');

  const [preferences, setPreferences] = useState<string[]>([
    'Open source',
    'Self-hosted',
    'Minimal operational overhead'
  ]);
  const [newPreferenceInput, setNewPreferenceInput] = useState('');

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [deploymentTarget, setDeploymentTarget] = useState('Docker on Single VM');
  const [latencyTarget, setLatencyTarget] = useState('< 30ms local feedback');
  const [teamSize, setTeamSize] = useState('3 engineers');
  const [existingStack, setExistingStack] = useState('React 19 + Go 1.24 + PostgreSQL');

  const handleApplyPreset = (preset: PresetTemplate) => {
    setObjective(preset.objective);
    setTechnologies([...preset.technologies]);
    setConstraints([...preset.constraints]);
    setScale(preset.scale);
    setBudget(preset.budget);
    setPreferences([...preset.preferences]);
    setDeploymentTarget(preset.advanced.deploymentTarget);
    setLatencyTarget(preset.advanced.latencyTarget);
    setTeamSize(preset.advanced.teamSize);
    setExistingStack(preset.advanced.existingStack);
  };

  const handleAddTech = () => {
    const val = newTechInput.trim();
    if (val && !technologies.includes(val)) {
      setTechnologies([...technologies, val]);
      setNewTechInput('');
    }
  };

  const handleAddConstraint = () => {
    const val = newConstraintInput.trim();
    if (val && !constraints.includes(val)) {
      setConstraints([...constraints, val]);
      setNewConstraintInput('');
    }
  };

  const handleAddPreference = () => {
    const val = newPreferenceInput.trim();
    if (val && !preferences.includes(val)) {
      setPreferences([...preferences, val]);
      setNewPreferenceInput('');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!objective.trim()) return;

    onStart({
      objective: objective.trim(),
      technologies,
      constraints,
      scale,
      budget,
      preferences,
      advanced: {
        deploymentTarget,
        latencyTarget,
        teamSize,
        existingStack
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-2">
      {/* Header Banner */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex items-center gap-2 text-xs font-mono text-blue-400 mb-2">
          <Compass className="w-4 h-4 text-blue-400" />
          <span>TECHNICAL INVESTIGATION BRIEF</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
          What are you building?
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl font-sans">
          Define your architectural objective and constraints. DEVSCOUT will decompose the problem, query web standards, inspect production repositories, and synthesize an evidence-backed decision report.
        </p>

        {/* Quick Presets Bar */}
        <div className="mt-5 pt-4 border-t border-slate-800/80">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-2">
            Load Architectural Spike Presets
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {PRESET_TEMPLATES.map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="text-left p-2.5 bg-[#0F1420] hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-md transition-colors"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-200 mb-0.5">
                  <span>{preset.name}</span>
                  <Zap className="w-3 h-3 text-blue-400" />
                </div>
                <p className="text-[11px] text-slate-400 truncate">
                  {preset.tagline}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Research Objective Textarea */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <label htmlFor="objective-input" className="font-semibold text-slate-200">
              Technical Research Objective <span className="text-rose-400">*</span>
            </label>
            <span className="text-[11px] font-mono text-slate-400">
              Be specific about technical domains and concurrency goals
            </span>
          </div>
          <div className="relative">
            <textarea
              id="objective-input"
              rows={4}
              required
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="e.g. Build a real-time collaborative whiteboard using React and Go supporting concurrent drawing, multi-cursor presence, and persistent room state..."
              className="w-full bg-[#0D121D] border border-slate-700/80 focus:border-blue-500 rounded-lg p-3.5 text-sm text-slate-100 placeholder-slate-500 font-sans focus:outline-hidden leading-relaxed"
            />
          </div>
        </div>

        {/* Structured Context Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 p-5 bg-[#0F1420] border border-slate-800 rounded-lg">
          {/* Technologies */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">
              Candidate Technologies & Languages
            </label>
            <div className="flex flex-wrap items-center gap-1.5 min-h-[38px] p-2 bg-[#090D15] border border-slate-800 rounded-md">
              {technologies.map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-950/70 border border-blue-800/60 text-blue-300 rounded text-xs font-mono"
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => setTechnologies(technologies.filter(t => t !== tech))}
                    className="hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <div className="flex items-center gap-1 flex-1 min-w-[120px]">
                <input
                  type="text"
                  value={newTechInput}
                  onChange={(e) => setNewTechInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTech();
                    }
                  }}
                  placeholder="+ Add technology"
                  className="w-full bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-hidden px-1"
                />
              </div>
            </div>
            {/* Quick Suggestions */}
            <div className="flex flex-wrap gap-1 text-[11px] text-slate-400">
              <span className="font-mono text-[10px]">Suggestions:</span>
              {TECH_SUGGESTIONS.filter(t => !technologies.includes(t)).slice(0, 5).map(tech => (
                <button
                  key={tech}
                  type="button"
                  onClick={() => setTechnologies([...technologies, tech])}
                  className="hover:text-slate-200 hover:underline"
                >
                  +{tech}
                </button>
              ))}
            </div>
          </div>

          {/* Constraints */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">
              Hard Constraints & Boundaries
            </label>
            <div className="flex flex-wrap items-center gap-1.5 min-h-[38px] p-2 bg-[#090D15] border border-slate-800 rounded-md">
              {constraints.map((c) => (
                <span
                  key={c}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-900 border border-slate-700/80 text-slate-300 rounded text-xs"
                >
                  {c}
                  <button
                    type="button"
                    onClick={() => setConstraints(constraints.filter(item => item !== c))}
                    className="hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <div className="flex items-center gap-1 flex-1 min-w-[120px]">
                <input
                  type="text"
                  value={newConstraintInput}
                  onChange={(e) => setNewConstraintInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddConstraint();
                    }
                  }}
                  placeholder="+ Add constraint"
                  className="w-full bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-hidden px-1"
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-1 text-[11px] text-slate-400">
              <span className="font-mono text-[10px]">Suggestions:</span>
              {CONSTRAINT_SUGGESTIONS.filter(c => !constraints.includes(c)).slice(0, 3).map(c => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setConstraints([...constraints, c])}
                  className="hover:text-slate-200 hover:underline"
                >
                  +{c}
                </button>
              ))}
            </div>
          </div>

          {/* Scale */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 block">
              Concurrency & Scale Target
            </label>
            <select
              value={scale}
              onChange={(e) => setScale(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-md p-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500"
            >
              <option value="~1,000 concurrent users">~1,000 concurrent users</option>
              <option value="~10,000 concurrent users">~10,000 concurrent users</option>
              <option value="50,000 events/second peak">50,000 events/second peak</option>
              <option value="100,000+ daily active users">100,000+ daily active users</option>
              <option value="Internal tooling / Small team (< 50 users)">Internal tooling / Small team (&lt; 50 users)</option>
            </select>
          </div>

          {/* Budget */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 block">
              Budget & Infrastructure Tier
            </label>
            <select
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-md p-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500"
            >
              <option value="Low / Bootstrapped">Low / Bootstrapped ($20-$50/month)</option>
              <option value="Moderate">Moderate ($150-$500/month)</option>
              <option value="Growth / Scale">Growth ($1,000-$5,000/month)</option>
              <option value="Enterprise / Dedicated">Enterprise / Dedicated infra</option>
            </select>
          </div>

          {/* Preferences */}
          <div className="md:col-span-2 space-y-2 pt-2 border-t border-slate-800">
            <label className="text-xs font-semibold text-slate-300 block">
              Architectural Preferences
            </label>
            <div className="flex flex-wrap items-center gap-1.5 min-h-[38px] p-2 bg-[#090D15] border border-slate-800 rounded-md">
              {preferences.map((p) => (
                <span
                  key={p}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 rounded text-xs font-mono"
                >
                  {p}
                  <button
                    type="button"
                    onClick={() => setPreferences(preferences.filter(item => item !== p))}
                    className="hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <div className="flex items-center gap-1 flex-1 min-w-[120px]">
                <input
                  type="text"
                  value={newPreferenceInput}
                  onChange={(e) => setNewPreferenceInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddPreference();
                    }
                  }}
                  placeholder="+ Add preference"
                  className="w-full bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-hidden px-1"
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-1 text-[11px] text-slate-400">
              <span className="font-mono text-[10px]">Suggestions:</span>
              {PREFERENCE_SUGGESTIONS.filter(p => !preferences.includes(p)).slice(0, 3).map(p => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPreferences([...preferences, p])}
                  className="hover:text-slate-200 hover:underline"
                >
                  +{p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Collapsible Advanced Requirements */}
        <div className="border border-slate-800/80 rounded-lg overflow-hidden bg-[#0A0E17]">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full p-3.5 flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-900/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              <span>Advanced Requirements & Existing Stack</span>
            </div>
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showAdvanced && (
            <div className="p-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">DEPLOYMENT TARGET</label>
                <input
                  type="text"
                  value={deploymentTarget}
                  onChange={(e) => setDeploymentTarget(e.target.value)}
                  placeholder="e.g. Single VM, Kubernetes, AWS ECS, Edge"
                  className="w-full bg-[#111624] border border-slate-700/80 rounded p-2 text-slate-200"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">LATENCY SLA</label>
                <input
                  type="text"
                  value={latencyTarget}
                  onChange={(e) => setLatencyTarget(e.target.value)}
                  placeholder="e.g. < 30ms local, < 100ms e2e"
                  className="w-full bg-[#111624] border border-slate-700/80 rounded p-2 text-slate-200"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">TEAM SIZE & SKILLSET</label>
                <input
                  type="text"
                  value={teamSize}
                  onChange={(e) => setTeamSize(e.target.value)}
                  placeholder="e.g. 3 engineers, strong TypeScript & Go"
                  className="w-full bg-[#111624] border border-slate-700/80 rounded p-2 text-slate-200"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-mono text-[11px]">EXISTING REPO / STACK</label>
                <input
                  type="text"
                  value={existingStack}
                  onChange={(e) => setExistingStack(e.target.value)}
                  placeholder="e.g. Monorepo, React 19, PostgreSQL 16"
                  className="w-full bg-[#111624] border border-slate-700/80 rounded p-2 text-slate-200"
                />
              </div>
            </div>
          )}
        </div>

        {/* Primary CTA Button */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-400 font-mono">
            Pipeline: 8 verification stages · Web, GitHub & RAG
          </div>

          <button
            type="submit"
            disabled={isStarting || !objective.trim()}
            className="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-md shadow-md hover:shadow-blue-600/20 transition-all cursor-pointer"
          >
            <span>{isStarting ? 'Initiating Pipeline...' : 'Start Research'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
