// TypeScript types for simulation results

export interface SimulationBottleneck {
  component: string;
  reason: string;
  utilization: number;
  suggestion: string;
}

export interface SimulationResult {
  latency_p50: number;
  latency_p99: number;
  throughput: number;
  dropped_requests: number;
  bottlenecks: SimulationBottleneck[];
  heatmap: Record<string, number>;  // component_id → utilization (0–1)
}

export interface TrafficProfile {
  requests_per_sec: number;
  pattern: 'steady' | 'spike' | 'gradual';
  duration_sec: number;
}
