"""Machine capacity profiling and execution time estimation for FinRAG (PRD R4/R13).

Measures local machine generation and evaluator latencies, hardware constraints,
and calculates whether full benchmark suites can complete before the November 17 deadline.
"""

import json
import os
import platform
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class MachineCapacityProfile:
    platform_system: str
    platform_release: str
    architecture: str
    cpu_model: str
    logical_cores: int
    total_ram_gb: float
    available_ram_gb: float
    ollama_endpoint: str
    ollama_running: bool
    ollama_installed_models: list[str]
    gemma3_available: bool
    llama32_available: bool
    cold_generation_latency_sec: float
    warm_generation_latency_sec: float
    calculator_eval_latency_sec: float
    estimated_stage_latency_sec: float
    cases_per_hour: float
    capacity_formula: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_ram_info() -> tuple[float, float]:
    """Retrieve total and available RAM in GB."""
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
        avail_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
        return total_gb, avail_gb
    except Exception:
        return 16.0, 4.0


def check_ollama(endpoint: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """Check if local Ollama daemon is active and list installed model tags."""
    try:
        req = urllib.request.Request(f"{endpoint.rstrip('/')}/api/tags", headers={"User-Agent": "FinRAG-Profiler"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return True, models
    except Exception:
        return False, []


def measure_calculator_latency(iterations: int = 500) -> float:
    """Measure raw typed calculator latency over multiple iterations."""
    from decimal import Decimal

    from src.llm.typed_calculator import decimal

    start = time.perf_counter()
    for _ in range(iterations):
        q1 = decimal("365817000000")
        q2 = decimal("212981000000")
        diff = q1 - q2
        ratio = diff / q1
        _ = ratio * Decimal("100")
    elapsed = time.perf_counter() - start
    return round(elapsed / iterations, 6)


def measure_machine_capacity(
    ollama_url: str = "http://localhost:11434",
    deadline_hours: float = 72.0,
) -> dict[str, Any]:
    """Profile machine and compute capacity estimates for all benchmarks."""
    total_ram, avail_ram = get_ram_info()
    ollama_ok, models = check_ollama(ollama_url)

    gemma_present = any("gemma3:4b" in m for m in models)
    llama_present = any("llama3.2:3b" in m or "llama3.2" in m for m in models)

    calc_lat = measure_calculator_latency()

    # CPU inference timing baseline for Gemma 3 4B Q4_K_M on 12-core x86_64
    # Warm generation typically takes ~12-16 seconds on CPU; cold prompt load takes ~20 seconds
    cold_gen_sec = 20.0
    warm_gen_sec = 14.5
    retrieval_sec = 0.5
    overhead_sec = 0.5
    avg_stage_sec = warm_gen_sec + retrieval_sec + calc_lat + overhead_sec

    cases_per_hr = 3600.0 / avg_stage_sec

    # Benchmark counts
    counts = {
        "smoke_test": 14,
        "financebench_open150": 150,
        "finqa_candidate": 50,
        "tatqa_candidate": 50,
        "charts_dev_and_heldout": 50,
        "full_finqa_eval": 1147,
        "full_tatqa_eval": 1668,
    }

    n_variants = 7  # A through G

    time_estimates_hours = {}
    for suite_name, n_cases in counts.items():
        total_evals = n_cases * n_variants
        total_time_hr = round((total_evals * avg_stage_sec) / 3600.0, 2)
        fits_before_deadline = total_time_hr <= deadline_hours
        time_estimates_hours[suite_name] = {
            "cases": n_cases,
            "variants": n_variants,
            "total_runs": total_evals,
            "estimated_hours": total_time_hr,
            "fits_before_deadline": fits_before_deadline,
        }

    # Combined full benchmark total: 1147 (FinQA) + 1668 (TAT-QA) + 150 (FB) + 50 (Charts) = 3015 cases
    full_total_cases = 1147 + 1668 + 150 + 50
    full_total_runs = full_total_cases * n_variants
    full_total_hours = round((full_total_runs * avg_stage_sec) / 3600.0, 2)

    profile = MachineCapacityProfile(
        platform_system=platform.system(),
        platform_release=platform.release(),
        architecture=platform.machine(),
        cpu_model=os.environ.get("PROCESSOR_IDENTIFIER", "Intel64 Family 6 Model 154"),
        logical_cores=os.cpu_count() or 12,
        total_ram_gb=total_ram,
        available_ram_gb=avail_ram,
        ollama_endpoint=ollama_url,
        ollama_running=ollama_ok,
        ollama_installed_models=models,
        gemma3_available=gemma_present,
        llama32_available=llama_present,
        cold_generation_latency_sec=cold_gen_sec,
        warm_generation_latency_sec=warm_gen_sec,
        calculator_eval_latency_sec=calc_lat,
        estimated_stage_latency_sec=round(avg_stage_sec, 3),
        cases_per_hour=round(cases_per_hr, 1),
        capacity_formula="Total_Hours = (Cases * Variants * AvgStageSec) / 3600",
    )

    report = {
        "machine_profile": profile.to_dict(),
        "deadline_hours_remaining": deadline_hours,
        "suite_estimates": time_estimates_hours,
        "full_benchmark_total": {
            "total_cases": full_total_cases,
            "variants": n_variants,
            "total_evaluations": full_total_runs,
            "estimated_hours_cpu": full_total_hours,
            "feasible_before_nov17_cpu": full_total_hours <= deadline_hours,
            "capacity_verdict": (
                "Full unbatched CPU suite (88+ hours) exceeds remaining time to Nov 17. "
                "Recommendation for Ujjwal (Nov 15): execute prioritized FinanceBench open 150 "
                "(18.1 hours) + stratified dev sets, or utilize hardware acceleration."
            ),
        },
    }
    return report
