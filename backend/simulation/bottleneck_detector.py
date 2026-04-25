"""
Bottleneck detector — identifies overloaded components
and generates scaling suggestions.
"""
from __future__ import annotations

from typing import Dict, List

from simulation.models import Bottleneck, Component, ComponentMetrics

UTILIZATION_THRESHOLD = 0.80  # components above this are flagged


def detect_bottlenecks(
    components: List[Component],
    metrics: Dict[str, ComponentMetrics],
) -> List[Bottleneck]:
    bottlenecks: List[Bottleneck] = []

    for comp in components:
        m = metrics[comp.id]
        if m.utilization >= UTILIZATION_THRESHOLD:
            reason = "throughput_limit" if m.utilization > 0.9 else "high_utilization"
            suggestion = _suggest(comp)
            bottlenecks.append(
                Bottleneck(
                    component_id=comp.id,
                    reason=reason,
                    utilization=m.utilization,
                    suggestion=suggestion,
                )
            )

    # Rank by utilization (highest impact first)
    bottlenecks.sort(key=lambda b: b.utilization, reverse=True)
    return bottlenecks


def _suggest(comp: Component) -> str:
    if comp.type in ("database", "cache"):
        return "add_read_replicas"
    if comp.type == "queue":
        return "increase_consumer_count"
    if comp.type in ("api_gateway", "microservice", "load_balancer"):
        return f"scale_horizontally (current replicas={comp.replicas})"
    return "add_replicas"
