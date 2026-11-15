"""Benchmark package for FinRAG: versioned loaders, metrics, capacity, and runner."""

from .capacity import MachineCapacityProfile, measure_machine_capacity
from .loaders import (
    BenchmarkCase,
    GoldReference,
    load_benchmark,
    load_financebench_open150,
    load_finqa,
    load_tatqa,
)
from .metrics import EvaluatorMetrics, compute_all_metrics, compute_paired_intervals
from .runner import BenchmarkRunner, RunManifest

__all__ = [
    "BenchmarkCase",
    "GoldReference",
    "load_benchmark",
    "load_financebench_open150",
    "load_finqa",
    "load_tatqa",
    "EvaluatorMetrics",
    "compute_all_metrics",
    "compute_paired_intervals",
    "BenchmarkRunner",
    "RunManifest",
    "MachineCapacityProfile",
    "measure_machine_capacity",
]
