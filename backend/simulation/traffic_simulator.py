"""
Deterministic traffic simulator.

Generates a fixed sequence of requests and routes each one
through the design graph, accumulating latency and utilization.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np

from simulation.models import Component, Edge, TrafficProfile, ComponentMetrics


def build_graph(components: List[Component], edges: List[Edge]) -> nx.DiGraph:
    G = nx.DiGraph()
    for c in components:
        G.add_node(c.id, component=c)
    for e in edges:
        G.add_edge(e.source, e.target, weight=e.weight)
    return G


def _entry_nodes(G: nx.DiGraph) -> List[str]:
    """Nodes with no in-edges are entry points (e.g. API gateways)."""
    return [n for n in G.nodes if G.in_degree(n) == 0] or list(G.nodes)[:1]


def simulate_traffic(
    components: List[Component],
    edges: List[Edge],
    profile: TrafficProfile,
    rng_seed: int = 42,
) -> Tuple[List[float], Dict[str, ComponentMetrics]]:
    """
    Returns:
        latencies  – per-request latency list (ms)
        metrics    – per-component utilization/dropped counters
    """
    rng = np.random.default_rng(rng_seed)
    G = build_graph(components, edges)
    comp_map: Dict[str, Component] = {c.id: c for c in components}
    metrics: Dict[str, ComponentMetrics] = {c.id: ComponentMetrics(id=c.id) for c in components}

    # Total requests over simulation window
    total_requests = int(profile.requests_per_sec * profile.duration_sec)

    # Apply traffic pattern multiplier per second bucket
    def rps_at(t: float) -> float:
        if profile.pattern == "spike":
            return profile.requests_per_sec * (1 + 9 * math.exp(-((t - 10) ** 2) / 20))
        if profile.pattern == "gradual":
            return profile.requests_per_sec * (t / profile.duration_sec)
        return profile.requests_per_sec  # steady

    # Track per-component request counts (to derive utilization)
    request_counts: Dict[str, int] = {c.id: 0 for c in components}
    latencies: List[float] = []

    entry = _entry_nodes(G)

    for i in range(total_requests):
        t = i / profile.requests_per_sec  # simulated time
        effective_rps = rps_at(t)

        # Probabilistic drop at entry if RPS > capacity (scaled by replicas)
        start_node = rng.choice(entry)
        entry_comp = comp_map[start_node]
        if effective_rps > entry_comp.throughput * entry_comp.replicas:
            metrics[start_node].dropped_requests += 1
            continue

        # BFS traversal through graph
        path = list(nx.bfs_tree(G, start_node).nodes)
        request_latency = 0.0
        dropped = False

        for node in path:
            comp = comp_map[node]
            request_counts[node] += 1
            utilization = request_counts[node] / (
                profile.requests_per_sec * profile.duration_sec / len(components)
            )
            metrics[node].utilization = min(utilization, 1.0)

            # Drop if throughput exceeded
            capacity = comp.throughput * comp.replicas
            if request_counts[node] > capacity * profile.duration_sec:
                metrics[node].dropped_requests += 1
                dropped = True
                break

            request_latency += comp.latency_ms + rng.exponential(comp.latency_ms * 0.1)

        if not dropped:
            latencies.append(request_latency)

    # Compute avg latency per component from utilization proxy
    for c in components:
        metrics[c.id].avg_latency_ms = c.latency_ms * (1 + metrics[c.id].utilization)

    return latencies, metrics
