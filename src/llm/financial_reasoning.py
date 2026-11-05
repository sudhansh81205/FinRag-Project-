"""
Financial Math Verification & Programmatic Reasoning (Member 3: LLM Integration Specialist)
Provides safe mathematical verification for financial formulas (YoY growth, margins, ratios).
"""

import math
import re
from typing import Any


def _finite_numbers(*values):
    try:
        return all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
                   for x in values)
    except OverflowError:
        return False


class FinancialMathVerifier:
    """
    Programmatic math verifier to prevent LLM hallucinations during numerical calculations.
    Computes exact YoY growth, gross margins, and percentage changes.
    """

    @staticmethod
    def calculate_yoy_growth(current_val: float, prior_val: float) -> dict[str, Any]:
        """Calculates Year-over-Year growth percentage."""
        if not _finite_numbers(current_val, prior_val):
            return {"error": "Values must be finite numbers", "growth_percentage": None}
        if prior_val == 0:
            return {"error": "Division by zero (prior value is 0)", "growth_pct": None,
                    "growth_percentage": None}
        change = current_val - prior_val
        if not _finite_numbers(change):
            return {"error": "Calculation exceeds finite numeric range", "growth_percentage": None}
        if prior_val < 0:
            return {"current": current_val, "prior": prior_val, "absolute_change": change,
                    "growth_percentage": None, "formula": f"{current_val} - ({prior_val})",
                    "explanation": "Ordinary growth is not reported for a negative prior; use absolute change."}
        growth_pct = (change / prior_val) * 100.0
        if not _finite_numbers(growth_pct):
            return {"error": "Calculation exceeds finite numeric range", "growth_percentage": None}
        return {
            "current": current_val,
            "prior": prior_val,
            "absolute_change": change,
            "growth_percentage": round(growth_pct, 2),
            "formula": f"(({current_val} - {prior_val}) / {prior_val}) * 100",
        }

    @staticmethod
    def calculate_margin(metric_value: float, total_revenue: float) -> dict[str, Any]:
        """Calculates profit or operating margin percentage."""
        if not _finite_numbers(metric_value, total_revenue):
            return {"error": "Values must be finite numbers", "margin_percentage": None}
        if total_revenue == 0:
            return {"error": "Division by zero (revenue is 0)", "margin_pct": None,
                    "margin_percentage": None}
        margin_pct = (metric_value / total_revenue) * 100.0
        if not _finite_numbers(margin_pct):
            return {"error": "Calculation exceeds finite numeric range", "margin_percentage": None}
        return {
            "metric": metric_value,
            "revenue": total_revenue,
            "margin_percentage": round(margin_pct, 2),
            "formula": f"({metric_value} / {total_revenue}) * 100",
        }

    @staticmethod
    def parse_currency_amount(raw_str: str) -> float | None:
        """Parse USD-style amounts into base units; explicit K/M/B scale once.

        This legacy helper is not a typed, cited calculator or a unit inference engine.
        """
        if not isinstance(raw_str, str) or not raw_str.strip():
            return None
        clean = raw_str.strip()
        negative = False
        if clean.startswith("(") and clean.endswith(")"):
            negative, clean = True, clean[1:-1].strip()
        match = re.fullmatch(r"\$?\s*([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*([KMB]?)", clean, re.I)
        if not match or (negative and match[1].startswith(("-", "+"))):
            return None
        amount = float(match[1].replace(",", "")) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[match[2].upper()]
        return (-amount if negative else amount) if math.isfinite(amount) else None
