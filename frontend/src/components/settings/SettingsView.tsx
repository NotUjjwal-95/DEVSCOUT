import React, { useState } from 'react';
import { researchService, DevscoutSettings } from '../../services/researchService';
import {
  Settings as SettingsIcon,
  Server,
  Database,
  Check,
  RotateCcw,
  Globe,
  GitFork,
  BookOpen,
  Sliders,
  ShieldCheck
} from 'lucide-react';

interface SettingsViewProps {
  onResetSeed: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onResetSeed }) => {
  const [settings, setSettings] = useState<DevscoutSettings>(researchService.getSettings());
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    researchService.saveSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-blue-400" />
          Settings & Engine Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure backend API endpoints, search crawler depth, and multi-source probe adapters.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Backend REST API Connector */}
        <section className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-blue-400 mb-1">
                <Server className="w-4 h-4 text-blue-400" />
                <span>BACKEND REST API INTEGRATION</span>
              </div>
              <h2 className="text-sm font-semibold text-slate-100">
                Python Research Engine Endpoint
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                DEVSCOUT UI is designed to communicate with the standalone Python backend via standardized REST endpoints.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono text-slate-300 block">
              API BASE URL
            </label>
            <input
              type="text"
              value={settings.apiBaseUrl}
              onChange={(e) => setSettings({ ...settings, apiBaseUrl: e.target.value })}
              placeholder="http://localhost:8000/api/v1"
              className="w-full bg-[#0A0E17] border border-slate-700 rounded-md p-2.5 text-xs font-mono text-slate-200 focus:outline-hidden focus:border-blue-500"
            />
            <span className="text-[11px] text-slate-400 block font-mono">
              Expected contracts: POST /research/start · GET /research/&#123;id&#125;/status · GET /research/&#123;id&#125;/evidence · GET /research/&#123;id&#125;/report
            </span>
          </div>

          <div className="flex items-center justify-between p-3 bg-slate-900/60 border border-slate-800 rounded-md">
            <div>
              <span className="text-xs font-semibold text-slate-200 block">
                Enable Remote Python Backend
              </span>
              <span className="text-[11px] text-slate-400">
                When disabled, the UI uses the high-fidelity local service layer.
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.useLiveBackend}
                onChange={(e) => setSettings({ ...settings, useLiveBackend: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-800 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </section>

        {/* Source Providers */}
        <section className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-mono text-blue-400 mb-1">
            <Database className="w-4 h-4 text-blue-400" />
            <span>SOURCE RETRIEVAL MODULES</span>
          </div>
          <h2 className="text-sm font-semibold text-slate-100">
            Active Multi-Source Probes
          </h2>

          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-slate-900/40 border border-slate-800/80 rounded-md">
              <div className="flex items-center gap-2.5">
                <Globe className="w-4 h-4 text-blue-400" />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Web & Official Documentation Crawler</span>
                  <span className="text-[11px] text-slate-400">Fetches standards, RFC specifications, and published benchmarks</span>
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings.enableWebSearch}
                onChange={(e) => setSettings({ ...settings, enableWebSearch: e.target.checked })}
                className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-900/40 border border-slate-800/80 rounded-md">
              <div className="flex items-center gap-2.5">
                <GitFork className="w-4 h-4 text-emerald-400" />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">GitHub Repository & Code Audit</span>
                  <span className="text-[11px] text-slate-400">Inspects commit cadences, open issues, and implementation architectures</span>
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings.enableGithubAudit}
                onChange={(e) => setSettings({ ...settings, enableGithubAudit: e.target.checked })}
                className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-900/40 border border-slate-800/80 rounded-md">
              <div className="flex items-center gap-2.5">
                <BookOpen className="w-4 h-4 text-cyan-400" />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Internal RAG Knowledge Base</span>
                  <span className="text-[11px] text-slate-400">Vector similarity over peer-reviewed architecture trade-offs</span>
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings.enableInternalRag}
                onChange={(e) => setSettings({ ...settings, enableInternalRag: e.target.checked })}
                className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
              />
            </div>
          </div>
        </section>

        {/* Research Depth */}
        <section className="bg-[#0F1420] border border-slate-800 rounded-lg p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono text-blue-400">
            <Sliders className="w-4 h-4 text-blue-400" />
            <span>INVESTIGATION DEPTH</span>
          </div>
          <h2 className="text-sm font-semibold text-slate-100">
            Pipeline Rigor Level
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'standard', title: 'Standard Spike', desc: 'Fast turnaround (3-5 core sources, high-level trade-offs)' },
              { id: 'deep', title: 'Deep Architectural RFC', desc: 'Default (8-12 sources, code audits, trade-off matrix)' },
              { id: 'exhaustive', title: 'Exhaustive Audit', desc: 'Comprehensive benchmarking & memory profiling checks' }
            ].map(tier => (
              <label
                key={tier.id}
                className={`p-3 border rounded-md cursor-pointer transition-colors block ${
                  settings.researchDepth === tier.id
                    ? 'bg-blue-950/40 border-blue-600/70'
                    : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="depth"
                  value={tier.id}
                  checked={settings.researchDepth === tier.id}
                  onChange={() => setSettings({ ...settings, researchDepth: tier.id as any })}
                  className="sr-only"
                />
                <span className="text-xs font-semibold text-slate-200 block mb-1">
                  {tier.title}
                </span>
                <span className="text-[11px] text-slate-400 leading-snug block">
                  {tier.desc}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={onResetSeed}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-md transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo Sessions to Seed</span>
          </button>

          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-md transition-colors"
          >
            {saved ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : null}
            <span>{saved ? 'Settings Saved' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
