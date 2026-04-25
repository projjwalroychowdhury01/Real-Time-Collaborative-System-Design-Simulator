"""
Simulation engine unit tests.
"""
import pytest
from simulation.engine import run_simulation


SIMPLE_DESIGN = {
    "components": [
        {"id": "api1", "type": "api_gateway", "replicas": 1, "throughput": 500, "latency_ms": 10},
        {"id": "db1",  "type": "database",    "replicas": 1, "throughput": 200, "latency_ms": 50},
    ],
    "edges": [{"from": "api1", "to": "db1", "weight": 1.0}],
}


def test_simulation_returns_required_keys():
    result = run_simulation(SIMPLE_DESIGN, {"requests_per_sec": 50, "pattern": "steady", "duration_sec": 10})
    assert "latency_p50" in result
    assert "latency_p99" in result
    assert "throughput" in result
    assert "bottlenecks" in result
    assert "heatmap" in result


def test_heatmap_contains_all_components():
    result = run_simulation(SIMPLE_DESIGN, {"requests_per_sec": 50, "pattern": "steady", "duration_sec": 10})
    assert "api1" in result["heatmap"]
    assert "db1"  in result["heatmap"]


def test_overloaded_db_detected_as_bottleneck():
    overloaded = {
        "components": [
            {"id": "api1", "type": "api_gateway", "replicas": 4, "throughput": 5000, "latency_ms": 5},
            {"id": "db1",  "type": "database",    "replicas": 1, "throughput": 10,   "latency_ms": 50},
        ],
        "edges": [{"from": "api1", "to": "db1", "weight": 1.0}],
    }
    result = run_simulation(overloaded, {"requests_per_sec": 200, "pattern": "steady", "duration_sec": 30})
    bottleneck_ids = [b["component"] for b in result["bottlenecks"]]
    assert "db1" in bottleneck_ids
