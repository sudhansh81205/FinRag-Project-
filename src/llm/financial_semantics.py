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
TOTAL_REVENUE_LABELS = frozenset({"total net sales", "total revenue", "total revenues", "net sales",
                                 "revenue", "revenues", "net revenue", "net revenues"})


def is_revenue_lookup(question):
    return (isinstance(question, str)
            and bool(re.search(r"\b(revenues?|net sales)\b", question, re.I))
            and bool(re.search(r"\b(how much|what (?:was|were)|reported?|report)\b", question, re.I))
            and not re.search(r"\b(growth|change|increase|decrease|percent|percentage|ratio|margin|share|compare|versus|vs)\b", question, re.I))


def total_revenue_fact(record):
    headers = record.get("metadata", {}).get("row_headers", [])
    label = headers[-1].strip() if isinstance(headers, list) and headers else ""
    # Printed statement footnote markers remain in the original row text. They do
    # not turn a consolidated total into a product/service component (IBM 2024).
    label = re.sub(r"\s+(?:[A-Z]|\([A-Za-z0-9]{1,2}\))$", "", label)
    return (role(record) == "revenue" and isinstance(headers, list) and bool(headers)
            and re.sub(r"\s+", " ", label.lower()).strip(":") in TOTAL_REVENUE_LABELS)


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
    metric = named_metric(question)
    if metric:
        expression = program.get("expression") if isinstance(program, dict) else None
        by_id = {record.get("evidence_id", record.get("id")): record for record in records}
        def valid_leaf(node):
            return isinstance(node, dict) and set(node) == {"evidence_id"} and metric_fact(question, by_id.get(node.get("evidence_id"), {}))
        if is_margin_comparison(question):
            expected = "percent_change" if re.search(r"\b(growth|percent|percentage)\b", question, re.I) else "change"
            if not isinstance(expression, dict) or expression.get("op") != expected or len(expression.get("args", [])) != 2 or not all(valid_leaf(n) for n in expression["args"]):
                return "Metric comparison requires matching source values and the requested change operation."
        elif not valid_leaf(expression):
            return "Requested total metric requires an included original source cell; component or different metrics cannot substitute."
        return ""
    if not is_gross_margin(question):
        return ""
    if is_margin_comparison(question):
        expression = program.get("expression") if isinstance(program, dict) else None
        if not isinstance(expression, dict) or expression.get("op") != "percentage_point_change" or len(expression.get("args", [])) != 2:
            return "Gross-margin changes require two source-bound margins and a percentage-point change formula."
        return next((problem for node in expression["args"] if (problem := validate_named_formula("gross margin", {"expression": node}, records))), "")
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
    revenue_lookup = is_revenue_lookup(question)
    if not isinstance(request, dict):
        return None
    if named_metric(question):
        leaves = []
        for period in sorted(request.get("periods", []), key=lambda p: p.get("end", "")):
            values = [r for r in records if metric_fact(question, r)
                      and r.get("metadata", {}).get("company") == request.get("issuer")
                      and r["metadata"].get("scope") == request.get("scope")
                      and {"kind": r["metadata"].get("period_kind"), "start": r["metadata"].get("period_start"), "end": r["metadata"].get("period_end")} == period]
            if len(values) > 1 and named_metric(question) != REVENUE:
                identities = {(r["metadata"].get("metric"), r["metadata"].get("normalized_unit"), r["metadata"].get("normalized_value_decimal")) for r in values}
                if len(identities) == 1 and all(all(key is not None for key in identity) for identity in identities):
                    values = [min(values, key=lambda r: r.get("evidence_id", ""))]
            if len(values) != 1:
                return None
            leaves.append({"evidence_id": values[0].get("evidence_id", values[0].get("id"))})
        if is_margin_comparison(question):
            if len(leaves) != 2:
                return None
            op = "percent_change" if re.search(r"\b(growth|percent|percentage)\b", question, re.I) else "change"
            return {**request, "expression": {"op": op, "args": [leaves[1], leaves[0]]}}
        return {**request, "expression": leaves[0]} if len(leaves) == 1 else None
    if is_gross_margin(question) and is_margin_comparison(question):
        periods = sorted(request.get("periods", []), key=lambda p: p.get("end", ""))
        if len(periods) != 2:
            return None
        levels = [known_source_program("gross margin", {**request, "periods": [p]}, records) for p in periods]
        if any(level is None for level in levels):
            return None
        return {**request, "expression": {"op": "percentage_point_change", "args": [levels[1]["expression"], levels[0]["expression"]]}}
    if not revenue_lookup and not is_gross_margin(question):
        return None
    periods = request.get("periods", [])
    facts = {"revenue": [], "cost": [], "gross_profit": []}
    for r in records:
        m = r.get("metadata", {})
        kind = role(r)
        if revenue_lookup and not total_revenue_fact(r):
            continue
        period = {"kind": m.get("period_kind"), "start": m.get("period_start"), "end": m.get("period_end")}
        if (kind and m.get("company") == request.get("issuer") and m.get("scope") == request.get("scope")
                and period in periods):
            facts[kind].append({"evidence_id": r.get("evidence_id", r.get("id"))})
    if len(facts["revenue"]) != 1:
        return None
    revenue = facts["revenue"][0]
    if revenue_lookup:
        return {**request, "expression": revenue}
    if len(facts["gross_profit"]) == 1:
        numerator = facts["gross_profit"][0]
    elif len(facts["cost"]) == 1 and not facts["gross_profit"]:
        numerator = {"op": "subtract", "args": [revenue, facts["cost"][0]]}
    else:
        return None
    return {**request, "expression": {"op": "ratio_percent", "args": [numerator, revenue]}}


def named_metric(question):
    patterns = [
        (r'\b(?:revenues?|net sales)\b', REVENUE),
        (r'\bnet income\b', frozenset({'NetIncomeLoss'})),
        (r'\boperating income\b', frozenset({'OperatingIncomeLoss'})),
        (r'\btotal assets\b', frozenset({'Assets'})),
        (r'\btotal liabilities\b', frozenset({'Liabilities'})),
        (r"\b(?:stockholders|shareholders).*equity\b", frozenset({'StockholdersEquity'})),
    ]
    if is_gross_margin(question):
        return None
    for pattern, metrics in patterns:
        if re.search(pattern, question, re.I):
            return metrics
    return None


def metric_fact(question, record):
    metrics = named_metric(question)
    m = record.get('metadata', {})
    if not metrics or m.get('type') != 'table_cell' or m.get('metric', '').split(':')[-1] not in metrics:
        return False
    return total_revenue_fact(record) if metrics == REVENUE else True


def interactive_source_fact(question, record):
    return ((role(record) in {'gross_profit', 'cost'} or total_revenue_fact(record))
            if is_gross_margin(question) else metric_fact(question, record))
