"""
Simulation engine entry point.

Parses design_json + traffic_profile dicts,
runs the traffic simulator and bottleneck detector,
and returns a structured result dict.
"""
from __future__ import annotations

import numpy as np
from typing import Any, Dict

from simulation.models import Component, Edge, TrafficProfile
from simulation.traffic_simulator import simulate_traffic
from simulation.bottleneck_detector import detect_bottlenecks


def run_simulation(design_json: Dict[str, Any], traffic_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        design_json:      { "components": [...], "edges": [...] }
        traffic_profile:  { "requests_per_sec": 100, "pattern": "steady", "duration_sec": 60 }

    Returns:
        Simulation result dict matching the API contract.
    """
    # Parse inputs
    components = [
        Component(
            id=c["id"],
            type=c.get("type", "microservice"),
            replicas=c.get("replicas", 1),
            throughput=c.get("throughput", 1000),
            latency_ms=c.get("latency_ms", 10),
        )
        for c in design_json.get("components", [])
    ]
    edges = [
        Edge(source=e["from"], target=e["to"], weight=e.get("weight", 1.0))
        for e in design_json.get("edges", [])
    ]
    profile = TrafficProfile(**traffic_profile)

    # Run simulation
    latencies, metrics = simulate_traffic(components, edges, profile)

    # Aggregate
    if latencies:
        lat_arr = np.array(latencies)
        p50 = float(np.percentile(lat_arr, 50))
        p99 = float(np.percentile(lat_arr, 99))
        throughput = len(latencies) / profile.duration_sec
    else:
        p50 = p99 = 0.0
        throughput = 0.0

    total_dropped = sum(m.dropped_requests for m in metrics.values())
    bottlenecks = detect_bottlenecks(components, metrics)

    return {
        "latency_p50": round(p50, 2),
        "latency_p99": round(p99, 2),
        "throughput": round(throughput, 2),
        "dropped_requests": total_dropped,
        "bottlenecks": [
            {
                "component": b.component_id,
                "reason": b.reason,
                "utilization": round(b.utilization, 3),
                "suggestion": b.suggestion,
            }
            for b in bottlenecks
        ],
        "heatmap": {cid: round(m.utilization, 3) for cid, m in metrics.items()},
    }
