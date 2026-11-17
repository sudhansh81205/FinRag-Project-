"""R5: license a named financial formula by metric meaning, not units alone.

Gross margin is gross profit / revenue (or (revenue - cost of sales) / revenue).
Subtracting revenue from an already reported gross-profit fact is arithmetically
valid but answers a different question. These predicates are fixed across variants
and read only actual included source cells, never benchmark labels or answers.
"""

import re

REVENUE = frozenset({"Revenue", "Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"})
COST = frozenset({"CostOfSales", "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"})
GROSS_PROFIT = frozenset({"GrossProfit"})


def is_gross_margin(question):
    return isinstance(question, str) and bool(re.search(r"\bgross\s+(?:profit\s+)?margin\b", question, re.I))


def is_margin_comparison(question):
    return bool(re.search(r"\b(change|changed|increase|increased|decrease|decreased|difference|growth|compare|compared|versus|vs)\b", question, re.I))


def role(record):
    metadata = record.get("metadata", {})
    if metadata.get("type") != "table_cell":
        return None
    metric = metadata.get("metric", "").split(":")[-1]
    return "revenue" if metric in REVENUE else "cost" if metric in COST else "gross_profit" if metric in GROSS_PROFIT else None


def validate_named_formula(question, program, records):
    """Return a refusal reason for a recognized metric whose formula is wrong."""
    if not is_gross_margin(question):
        return ""
    if is_margin_comparison(question):
        return "Gross-margin changes require independently bound comparison periods and a supported comparison formula."
    by_id = {r.get("evidence_id", r.get("id")): r for r in records}

    def leaf_role(node):
        if isinstance(node, dict) and set(node) == {"evidence_id"}:
            return role(by_id.get(node["evidence_id"], {}))
        return None

    expression = program.get("expression") if isinstance(program, dict) else None
    if not isinstance(expression, dict) or expression.get("op") != "ratio_percent":
        return "Gross margin percentage requires a gross-profit/revenue percentage formula."
    args = expression.get("args")
    if not isinstance(args, list) or len(args) != 2 or leaf_role(args[1]) != "revenue":
        return "Gross margin denominator must be a cited revenue fact."
    numerator = args[0]
    if leaf_role(numerator) == "gross_profit":
        return ""
    if isinstance(numerator, dict) and numerator.get("op") == "subtract":
        operands = numerator.get("args")
        if (isinstance(operands, list) and len(operands) == 2
                and leaf_role(operands[0]) == "revenue" and leaf_role(operands[1]) == "cost"):
            return ""
    return "Gross margin numerator must be reported gross profit or revenue minus cost of sales; the proposed metric meanings differ."


def known_source_program(question, request, records):
    """A bounded source-driven formula for recognized gross margin; no numeric constants.

    A unique included gross-profit and revenue pair is preferred. Without it, a
    unique revenue/cost pair is admissible. Ambiguous or absent facts produce no
    program; the caller must refuse or validate its untrusted proposal separately.
    """
    if not is_gross_margin(question) or is_margin_comparison(question) or not isinstance(request, dict):
        return None
    periods = request.get("periods", [])
    facts = {"revenue": [], "cost": [], "gross_profit": []}
    for r in records:
        m = r.get("metadata", {})
        kind = role(r)
        period = {"kind": m.get("period_kind"), "start": m.get("period_start"), "end": m.get("period_end")}
        if (kind and m.get("company") == request.get("issuer") and m.get("scope") == request.get("scope")
                and period in periods):
            facts[kind].append({"evidence_id": r.get("evidence_id", r.get("id"))})
    if len(facts["revenue"]) != 1:
        return None
    revenue = facts["revenue"][0]
    if len(facts["gross_profit"]) == 1:
        numerator = facts["gross_profit"][0]
    elif len(facts["cost"]) == 1 and not facts["gross_profit"]:
        numerator = {"op": "subtract", "args": [revenue, facts["cost"][0]]}
    else:
        return None
    return {**request, "expression": {"op": "ratio_percent", "args": [numerator, revenue]}}
