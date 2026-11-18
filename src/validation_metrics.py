"""R7/R12 development metrics; these do not grant independent study acceptance."""
import random
from statistics import mean


def ranked_operand_metrics(ranked_ids, operand_groups):
    """Recall counts interchangeable original facts once per required operand.

    A group may contain repeated statement occurrences of the same typed value.
    Complete@k requires every operand; MRR concerns the first relevant operand.
    """
    if not operand_groups or any(not group for group in operand_groups):
        raise ValueError("A labelled retrieval case requires nonempty operand groups")
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("Duplicate IDs cannot improve a ranking")
    groups = [set(group) for group in operand_groups]
    relevant = set().union(*groups)
    result = {}
    for k in (5, 10):
        top = set(ranked_ids[:k])
        hits = sum(bool(group & top) for group in groups)
        result[f"recall_at_{k}"] = hits / len(groups)
        result[f"complete_at_{k}"] = int(hits == len(groups))
    result["mrr_at_10"] = next((1 / rank for rank, identity in enumerate(ranked_ids[:10], 1)
                                          if identity in relevant), 0.0)
    return result


def clustered_interval(rows, value_key, *, cluster_key="accession", seed=42, samples=10000):
    """Percentile interval by resampling whole filings, not correlated questions."""
    if not rows:
        return None
    groups = {}
    for row in rows:
        groups.setdefault(row[cluster_key], []).append(float(row[value_key]))
    keys = sorted(groups)
    rng = random.Random(seed)
    draws = sorted(mean(value for key in rng.choices(keys, k=len(keys)) for value in groups[key])
                   for _ in range(samples))
    return {"estimate": mean(float(row[value_key]) for row in rows),
            "low": draws[int(0.025 * (samples - 1))], "high": draws[int(0.975 * (samples - 1))],
            "confidence": 0.95, "resamples": samples, "seed": seed, "clusters": len(keys),
            "sampling_unit": "filing; development-set uncertainty only"}
