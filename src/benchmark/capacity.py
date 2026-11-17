"""Machine capacity profiling and execution-time estimation for FinRAG (PRD R4/R7/R13).

Empirical-AI rule (F31): a capacity number is only as real as the observation behind it.

* Hardware facts that cannot be read are ``None`` (unknown), never invented defaults.
* Retrieval/generation/evaluator seconds come from ``observed_timings`` -- a saved pilot with
  case IDs, timestamps and model identities. Without them every timing and every derived
  hours/cases-per-hour figure is ``None`` and feasibility is ``"unknown"``.
* Remaining time is computed from the wall clock to an explicit deadline. The deadline is
  user-requested and its official cutoff is unconfirmed, so that is reported with it.
* Estimates are ``cases x variants x seconds`` plus cold starts and an explicit retry
  fraction; missing evaluator time or retry overhead make the result a labelled lower bound.

Viva: which measured stages belong in the full-evaluation time budget?
"""

import json
import os
import platform
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IST = timezone(timedelta(hours=5, minutes=30))
DEFAULT_DEADLINE_ISO = "2026-11-17T23:59:00+05:30"
N_VARIANTS = 7  # A through G

# Locally inventoried suites (generated smoke fixtures) and PRD-declared but not locally
# inventoried full suites. Full sizes are declarations, not verified inventories.
LOCAL_SMOKE_SUITES = {"financebench_open150_fixture": 150, "finqa_candidate_fixture": 50,
                      "tatqa_candidate_fixture": 50, "chart_questions": 50}
DECLARED_UNVERIFIED_FULL_SUITES = {"finqa_full_test": 1147, "tatqa_full_eval": 1668}


@dataclass
class MachineCapacityProfile:
    platform_system: str
    platform_release: str
    architecture: str
    cpu_model: str | None
    logical_cores: int | None
    total_ram_gb: float | None
    available_ram_gb: float | None
    ollama_endpoint: str
    ollama_running: bool
    ollama_installed_models: list[str]
    gemma3_available: bool
    llama32_available: bool
    cold_generation_latency_sec: float | None
    warm_generation_latency_sec: float | None
    retrieval_latency_sec: float | None
    evaluator_latency_sec: float | None
    calculator_eval_latency_sec: float
    estimated_stage_latency_sec: float | None
    cases_per_hour: float | None
    capacity_formula: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_ram_info() -> tuple[float | None, float | None]:
    """Total and available RAM in GB, or (None, None) when it cannot be read."""
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return round(stat.ullTotalPhys / 1024 ** 3, 2), round(stat.ullAvailPhys / 1024 ** 3, 2)
    except Exception:
        pass
    try:  # POSIX
        page, pages = os.sysconf("SC_PAGE_SIZE"), os.sysconf("SC_PHYS_PAGES")
        avail = os.sysconf("SC_AVPHYS_PAGES")
        return round(page * pages / 1024 ** 3, 2), round(page * avail / 1024 ** 3, 2)
    except Exception:
        return None, None


def check_ollama(endpoint: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """Check if the local Ollama daemon is active and list installed model tags."""
    try:
        req = urllib.request.Request(f"{endpoint.rstrip('/')}/api/tags", headers={"User-Agent": "FinRAG-Profiler"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return False, []


def measure_calculator_latency(iterations: int = 500) -> float:
    """Measure raw typed calculator latency over multiple iterations (a real local measurement)."""
    from decimal import Decimal

    from src.llm.typed_calculator import decimal

    start = time.perf_counter()
    for _ in range(iterations):
        q1 = decimal("365817000000")
        q2 = decimal("212981000000")
        _ = ((q1 - q2) / q1) * Decimal("100")
    return round((time.perf_counter() - start) / iterations, 6)


def load_observed_timings(path: Path | str) -> dict[str, Any]:
    """Load a saved pilot (timings + pilot case IDs + timestamps + model identities)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_observations(observed: dict[str, Any] | None) -> tuple[dict[str, float | None], list[str]]:
    """Extract positive finite timings and list what is missing or unverifiable."""
    problems: list[str] = []
    timings: dict[str, float | None] = dict.fromkeys(
        ("cold_generation_sec", "warm_generation_sec", "retrieval_sec", "evaluator_sec"))
    if not observed:
        return timings, ["No observed pilot timings were supplied."]
    for key in timings:
        v = observed.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 < v < float("inf"):
            timings[key] = float(v)
    for key in ("pilot_case_ids", "measured_at", "model_identity"):
        if not observed.get(key):
            problems.append(f"Pilot record lacks '{key}'; timings are not auditable.")
    return timings, problems


def compute_capacity(
    suites: dict[str, int],
    timings: dict[str, float | None],
    hours_remaining: float,
    n_variants: int = N_VARIANTS,
    retry_overhead_fraction: float | None = None,
) -> dict[str, Any]:
    """Pure capacity formula: Hours = (cases*variants*per_case*(1+retry) + variants*cold)/3600.

    Per-case seconds need measured retrieval and warm generation. Missing evaluator seconds or
    retry overhead give a labelled lower bound; missing required timings give ``None``.
    """
    retrieval, warm = timings.get("retrieval_sec"), timings.get("warm_generation_sec")
    evaluator, cold = timings.get("evaluator_sec"), timings.get("cold_generation_sec")
    notes = []
    if retrieval is None or warm is None:
        return {"per_case_seconds": None, "cases_per_hour": None, "suite_estimates": {
                    name: {"cases": n, "variants": n_variants, "estimated_hours": None,
                           "fits_before_deadline": "unknown"} for name, n in suites.items()},
                "feasibility": "unknown",
                "notes": ["Required measured retrieval and warm-generation timings are absent."]}
    per_case = retrieval + warm + (evaluator or 0.0)
    if evaluator is None:
        notes.append("Evaluator (RAGAS) time unmeasured: lower bound.")
    if cold is None:
        notes.append("Cold-start time unmeasured: lower bound.")
    if retry_overhead_fraction is None:
        notes.append("Retry/failure overhead not declared: lower bound.")
    retry = retry_overhead_fraction or 0.0
    estimates = {}
    for name, n in suites.items():
        hours = (n * n_variants * per_case * (1 + retry) + n_variants * (cold or 0.0)) / 3600.0
        estimates[name] = {"cases": n, "variants": n_variants, "estimated_hours": round(hours, 2),
                           "fits_before_deadline": hours <= hours_remaining}
    total = sum(e["estimated_hours"] for e in estimates.values())
    return {"per_case_seconds": round(per_case, 3), "cases_per_hour": round(3600.0 / per_case, 1),
            "suite_estimates": estimates, "combined_hours": round(total, 2),
            "feasibility": "fits" if total <= hours_remaining else "does_not_fit",
            "lower_bound": bool(notes), "notes": notes}


def measure_machine_capacity(
    ollama_url: str = "http://localhost:11434",
    deadline_iso: str = DEFAULT_DEADLINE_ISO,
    observed_timings: dict[str, Any] | None = None,
    retry_overhead_fraction: float | None = None,
    now: datetime | None = None,
    case_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Profile the machine and derive capacity strictly from real observations."""
    total_ram, avail_ram = get_ram_info()
    ollama_ok, models = check_ollama(ollama_url)
    calc_lat = measure_calculator_latency()

    deadline = datetime.fromisoformat(deadline_iso)
    now = now or datetime.now(tz=IST)
    hours_remaining = max(0.0, (deadline - now).total_seconds() / 3600.0)

    timings, problems = validate_observations(observed_timings)
    suites = {**LOCAL_SMOKE_SUITES}
    if case_inventory is not None:
        suites = {name: item["total_cases"] for name, item in case_inventory["benchmarks"].items()}
        if not suites or any(type(n) is not int or n < 1 for n in suites.values()):
            raise ValueError("Capacity requires nonempty actual case counts")
        if sum(suites.values()) != case_inventory.get("total_selected_cases"):
            raise ValueError("Capacity case inventory total is inconsistent")
    capacity = compute_capacity(suites, timings, hours_remaining, N_VARIANTS, retry_overhead_fraction)

    profile = MachineCapacityProfile(
        platform_system=platform.system(),
        platform_release=platform.release(),
        architecture=platform.machine(),
        cpu_model=os.environ.get("PROCESSOR_IDENTIFIER") or platform.processor() or None,
        logical_cores=os.cpu_count(),
        total_ram_gb=total_ram,
        available_ram_gb=avail_ram,
        ollama_endpoint=ollama_url,
        ollama_running=ollama_ok,
        ollama_installed_models=models,
        gemma3_available=any("gemma3:4b" in m for m in models),
        llama32_available=any("llama3.2" in m for m in models),
        cold_generation_latency_sec=timings["cold_generation_sec"],
        warm_generation_latency_sec=timings["warm_generation_sec"],
        retrieval_latency_sec=timings["retrieval_sec"],
        evaluator_latency_sec=timings["evaluator_sec"],
        calculator_eval_latency_sec=calc_lat,
        estimated_stage_latency_sec=capacity["per_case_seconds"],
        cases_per_hour=capacity["cases_per_hour"],
        capacity_formula="Hours = (cases * variants * (retrieval + warm_generation + evaluator) * (1 + retry) "
                         "+ variants * cold_start) / 3600",
    )
    return {
        "machine_profile": profile.to_dict(),
        "measured_at": now.isoformat(),
        "deadline": {"iso": deadline_iso, "kind": "user_requested_submission_deadline",
                     "official_cutoff_confirmed": False, "hours_remaining": round(hours_remaining, 2)},
        "observation_status": "observed" if not problems and capacity["feasibility"] != "unknown" else "unknown",
        "observation_problems": problems,
        "pilot": {k: (observed_timings or {}).get(k) for k in ("pilot_case_ids", "measured_at", "model_identity")},
        "suite_inventory": {"local_smoke_fixtures": LOCAL_SMOKE_SUITES,
                            "declared_full_suites_not_inventoried": DECLARED_UNVERIFIED_FULL_SUITES,
                            "selected_actual_counts": suites if case_inventory is not None else None},
        "capacity": capacity,
        "note": ("Only the calculator latency is a local measurement. Retrieval, generation and evaluator timings "
                 "require a recorded pilot on the intended hardware with observed model identities; unavailable "
                 "services leave them unknown. Full-suite scope is not feasible-by-assumption."),
    }
