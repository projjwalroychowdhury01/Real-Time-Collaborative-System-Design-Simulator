import { useState } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useUIStore } from '@/store/uiStore';
import type { TrafficProfile } from '@/types/simulation';

export default function SimulationPanel() {
  const { runSimulation } = useSimulation();
  const { simulationResult, isSimulating } = useUIStore();

  const [profile, setProfile] = useState<TrafficProfile>({
    requests_per_sec: 100,
    pattern: 'steady',
    duration_sec: 60,
  });

  return (
    <div className="sim-panel card">
      <h3>Simulation</h3>

      <label>
        RPS
        <input type="number" value={profile.requests_per_sec}
          onChange={(e) => setProfile((p) => ({ ...p, requests_per_sec: +e.target.value }))} />
      </label>
      <label>
        Pattern
        <select value={profile.pattern}
          onChange={(e) => setProfile((p) => ({ ...p, pattern: e.target.value as any }))}>
          <option value="steady">Steady</option>
          <option value="spike">Spike</option>
          <option value="gradual">Gradual</option>
        </select>
      </label>
      <label>
        Duration (s)
        <input type="number" value={profile.duration_sec}
          onChange={(e) => setProfile((p) => ({ ...p, duration_sec: +e.target.value }))} />
      </label>

      <button
        id="run-simulation-btn"
        className="btn btn-primary"
        disabled={isSimulating}
        onClick={() => runSimulation(profile)}
      >
        {isSimulating ? 'Running…' : '▶ Run Simulation'}
      </button>

      {simulationResult && (
        <div className="sim-results">
          <div className="stat"><span>P50 Latency</span><strong>{simulationResult.latency_p50} ms</strong></div>
          <div className="stat"><span>P99 Latency</span><strong>{simulationResult.latency_p99} ms</strong></div>
          <div className="stat"><span>Throughput</span><strong>{simulationResult.throughput} req/s</strong></div>
          <div className="stat"><span>Dropped</span><strong>{simulationResult.dropped_requests}</strong></div>

          {simulationResult.bottlenecks.length > 0 && (
            <div className="bottlenecks">
              <h3>Bottlenecks</h3>
              {simulationResult.bottlenecks.map((b) => (
                <div key={b.component} className="bottleneck-item">
                  <strong>{b.component}</strong>
                  <span>{b.reason} ({Math.round(b.utilization * 100)}% util)</span>
                  <em>→ {b.suggestion}</em>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <style>{`
        .sim-panel { padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3); }
        .sim-panel label { display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem; color: var(--color-text-muted); }
        .sim-panel input, .sim-panel select { background: var(--color-surface-2); border: 1px solid var(--color-border); color: var(--color-text); padding: var(--space-2); border-radius: var(--radius-sm); font-family: var(--font-sans); }
        .sim-results { margin-top: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); }
        .stat { display: flex; justify-content: space-between; font-size: 0.85rem; padding: var(--space-2) 0; border-bottom: 1px solid var(--color-border); }
        .stat strong { color: var(--color-accent); }
        .bottlenecks { margin-top: var(--space-3); }
        .bottlenecks h3 { margin-bottom: var(--space-2); font-size: 0.85rem; color: var(--color-warning); }
        .bottleneck-item { background: var(--color-surface-2); border-left: 3px solid var(--color-warning); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); display: flex; flex-direction: column; gap: 2px; font-size: 0.8rem; margin-bottom: var(--space-2); }
        .bottleneck-item em { color: var(--color-accent); font-style: normal; }
      `}</style>
    </div>
  );
}
