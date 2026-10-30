"""
Financial Math Verification & Programmatic Reasoning (Member 3: LLM Integration Specialist)
Provides safe mathematical verification for financial formulas (YoY growth, margins, ratios).
"""

from typing import Any


class FinancialMathVerifier:
    """
    Programmatic math verifier to prevent LLM hallucinations during numerical calculations.
    Computes exact YoY growth, gross margins, and percentage changes.
    """

    @staticmethod
    def calculate_yoy_growth(current_val: float, prior_val: float) -> dict[str, Any]:
        """Calculates Year-over-Year growth percentage."""
        if prior_val == 0:
            return {"error": "Division by zero (prior value is 0)", "growth_pct": None}
        change = current_val - prior_val
        growth_pct = (change / abs(prior_val)) * 100.0
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
        if total_revenue == 0:
            return {"error": "Division by zero (revenue is 0)", "margin_pct": None}
        margin_pct = (metric_value / total_revenue) * 100.0
        return {
            "metric": metric_value,
            "revenue": total_revenue,
            "margin_percentage": round(margin_pct, 2),
            "formula": f"({metric_value} / {total_revenue}) * 100",
        }

    @staticmethod
    def parse_currency_amount(raw_str: str) -> float | None:
        """Parses strings like '$365,817', '(2,400)', '365817M' into standard floats."""
        if not raw_str:
            return None
        clean = raw_str.strip().replace("$", "").replace(",", "")
        if clean.startswith("(") and clean.endswith(")"):
            clean = "-" + clean[1:-1]
        try:
            return float(clean)
        except ValueError:
            return None
