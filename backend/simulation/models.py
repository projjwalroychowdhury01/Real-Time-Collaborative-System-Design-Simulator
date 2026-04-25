"""
Simulation data models.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Component:
    id: str
    type: str                     # 'api_gateway' | 'database' | 'cache' | 'queue' | 'microservice' | ...
    replicas: int = 1
    throughput: float = 1000      # max requests/sec the component can handle
    latency_ms: float = 10        # processing latency per request


@dataclass
class Edge:
    source: str
    target: str
    weight: float = 1.0           # relative traffic weight on this edge


@dataclass
class TrafficProfile:
    requests_per_sec: float = 100
    pattern: str = "steady"       # "steady" | "spike" | "gradual"
    duration_sec: int = 60


@dataclass
class ComponentMetrics:
    id: str
    utilization: float = 0.0      # 0 → 1
    avg_latency_ms: float = 0.0
    dropped_requests: int = 0


@dataclass
class Bottleneck:
    component_id: str
    reason: str                   # 'throughput_limit' | 'high_latency'
    utilization: float
    suggestion: str


@dataclass
class SimulationResult:
    latency_p50: float
    latency_p99: float
    throughput: float             # actual RPS delivered
    dropped_requests: int
    bottlenecks: List[Bottleneck]
    heatmap: dict                 # component_id → utilization (0–1)
