"""R5: bounded, cited Decimal arithmetic and deterministic KR&R predicates.

Only a declarative tree is accepted. Leaves resolve into actual included canonical
cells; constants, Python, functions and model-supplied numeric values are forbidden.
"""

import hashlib
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext


class RuleFailure(ValueError):
    def __init__(self, rule, message):
        super().__init__(message)
        self.rule = rule


def require(condition, rule, message):
    if not condition:
        raise RuleFailure(rule, message)


def decimal(value):
    require(isinstance(value, (str, int)) and not isinstance(value, bool),
            "finite_decimal", "An exact decimal string or integer is required.")
    require(len(str(value)) <= 80, "bounded_number", "Numeric input exceeds the bound.")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise RuleFailure("finite_decimal", "Invalid decimal.") from exc
    require(number.is_finite() and abs(number) < Decimal('1e40')
            and number.as_tuple().exponent >= -30,
            "bounded_number", "Nonfinite or excessive numeric value.")
    return number


@dataclass(frozen=True)
class Quantity:
    value: Decimal
    unit: str
    currency: str | None
    issuer: str
    scope: str
    period: tuple
    metrics: tuple
    ids: tuple
    expression: str


def period(value):
    require(isinstance(value, dict) and set(value) == {"kind", "start", "end"},
            "period", "Declare kind, start and end for every requested period.")
    try:
        end = date.fromisoformat(value["end"])
        start = date.fromisoformat(value["start"]) if value["start"] is not None else None
    except (TypeError, ValueError) as exc:
        raise RuleFailure("period", "Invalid period boundaries.") from exc
    require((value["kind"] == "instant" and start is None)
            or (value["kind"] == "duration" and start is not None and start <= end),
            "period", "Inconsistent period kind/boundaries.")
    return value["kind"], value["start"], value["end"]


def evaluate(plan, included_records):
    """Return an exact result or a recorded rule failure; never execute generated code.

    Plans explicitly bind issuer, scope and requested periods. `change` and
    `percent_change` compare adjacent fiscal years; other binary operations require
    the same period. Monetary division yields a dimensionless ratio. Arbitrary
    products of two monetary quantities are deliberately unsupported.
    """
    trace, operands, used = [], {}, set()
    try:
        require(isinstance(plan, dict) and set(plan) == {"issuer", "scope", "periods", "expression"},
                "plan_schema", "Declare issuer, scope, periods and expression only.")
        require(all(isinstance(plan[k], str) and plan[k].strip() for k in ("issuer", "scope")),
                "plan_schema", "Issuer and scope must be explicit.")
        require(isinstance(plan["periods"], list) and 1 <= len(plan["periods"]) <= 2,
                "period", "One or two explicitly requested periods are supported.")
        requested = [period(p) for p in plan["periods"]]
        require(len(set(requested)) == len(requested), "period", "Duplicate requested periods.")
        records = {}
        for record in included_records:
            identity = record.get("evidence_id", record.get("id"))
            require(identity not in records and record.get("id", identity) == identity,
                    "unique_citation", "Duplicate or conflicting evidence identity.")
            records[identity] = record
        nodes = 0

        def visit(node, depth=0):
            nonlocal nodes
            nodes += 1
            require(nodes <= 31 and depth <= 7, "bounded_tree", "Expression exceeds 31 nodes or depth 7.")
            require(isinstance(node, dict), "tree_schema", "An operation or cited leaf is required.")
            if set(node) == {"evidence_id"}:
                identity = node["evidence_id"]
                require(isinstance(identity, str) and identity in records,
                        "included_citation", "Operand is absent from the actual included context.")
                record = records[identity]
                m = record.get("metadata", {})
                require(m.get("type") == "table_cell", "typed_cell", "Only typed table cells can be operands.")
                require(isinstance(record.get("content"), str)
                        and hashlib.sha256(record["content"].encode()).hexdigest() == m.get("content_sha256"),
                        "content_integrity", "Cell content hash mismatch.")
                required = ("company", "metric", "scope", "table_title", "source_url", "source_locator", "accession")
                require(all(isinstance(m.get(k), str) and m[k] for k in required),
                        "fact_identity", "Cell identity or source provenance is incomplete.")
                require(m["company"] == plan["issuer"] and m["scope"] == plan["scope"],
                        "issuer_scope", "Operand issuer/scope does not match the request.")
                p = period({"kind": m.get("period_kind"), "start": m.get("period_start"), "end": m.get("period_end")})
                require(p in requested, "requested_period", "Operand period was not requested.")
                used.add(p)
                unit, currency = m.get("normalized_unit"), m.get("currency")
                require(unit in {"USD", "shares", "USD/share"} and m.get("unit") == unit,
                        "unit", "Unsupported or conflicting normalized unit.")
                require(currency == ("USD" if unit in {"USD", "USD/share"} else None),
                        "currency", "Currency/unit mismatch.")
                scale = m.get("scale_power10")
                require(type(scale) is int and -9 <= scale <= 12 and m.get("scale") == 10 ** scale,
                        "scale", "Invalid or conflicting scale.")
                raw = m.get("raw_value")
                require(isinstance(raw, str), "raw_value", "Missing displayed source value.")
                import re
                raw = raw.replace("$", "").replace(",", "").replace(" ", "")
                require(bool(re.fullmatch(r"(?:\(\d+(?:\.\d+)?\)|-?\d+(?:\.\d+)?)", raw)),
                        "raw_value", "Missing or ambiguous displayed number.")
                amount = decimal(raw.replace("(", "-").replace(")", "")).scaleb(scale)
                value = decimal(m.get("normalized_value_decimal"))
                require(value == amount and decimal(str(m.get("normalized_value"))) == value,
                        "normalization", "Raw, normalized decimal and JSON values disagree.")
                operands[identity] = {k: m.get(k) for k in (*required, "raw_value", "raw_unit", "normalized_unit", "currency", "scale_power10", "normalized_value_decimal", "period_kind", "period_start", "period_end")}
                trace.append({"rule_id": "cited_value_fact", "premises": [identity], "outcome": "pass"})
                return Quantity(value, unit, currency, m["company"], m["scope"], p,
                                (m["metric"],), (identity,), f"[{identity}]")
            require(set(node) == {"op", "args"} and isinstance(node["args"], list)
                    and len(node["args"]) == 2 and node["op"] in {
                        "add", "subtract", "multiply", "divide", "ratio_percent", "change", "percent_change"},
                    "allowed_operation", "Only allowlisted binary operation trees are accepted.")
            left, right = (visit(child, depth + 1) for child in node["args"])
            op = node["op"]
            require((left.issuer, left.scope) == (right.issuer, right.scope),
                    "comparable_identity", "Issuer or scope differs.")
            cross_period = op in {"change", "percent_change"}
            require(left.unit == right.unit and left.currency == right.currency
                    or op == "multiply" and "ratio" in (left.unit, right.unit),
                    "comparable_units", "Operands have incompatible units/currency.")
            if cross_period:
                require(left.metrics == right.metrics and left.unit != "percent",
                        "comparable_metric", "Annual comparison requires matching metric meaning.")
                require(left.period[0] == right.period[0]
                        and date.fromisoformat(left.period[2]).year == date.fromisoformat(right.period[2]).year + 1
                        and 350 <= (date.fromisoformat(left.period[2]) - date.fromisoformat(right.period[2])).days <= 380,
                        "annual_periods", "Current/prior periods must be adjacent comparable fiscal years.")
                if left.period[0] == "duration":
                    lengths = [(date.fromisoformat(q.period[2]) - date.fromisoformat(q.period[1])).days for q in (left, right)]
                    require(min(lengths) >= 350 and max(lengths) <= 380 and abs(lengths[0] - lengths[1]) <= 7,
                            "annual_duration", "Quarterly or unequal duration comparison is unsupported.")
            else:
                require(left.period == right.period, "same_period", "Operation requires the same period.")
            require(left.unit != "percent" and right.unit != "percent", "percent_terminal", "Percentage outputs are terminal.")
            unit, currency = left.unit, left.currency
            note = None
            if op in {"add", "subtract", "change"}:
                value = left.value + right.value if op == "add" else left.value - right.value
            elif op == "multiply":
                require("ratio" in (left.unit, right.unit), "dimensionless_product", "Multiplication requires a dimensionless ratio.")
                value = left.value * right.value
                other = right if left.unit == "ratio" else left
                unit, currency = other.unit, other.currency
            else:
                require(right.value != 0, "nonzero_denominator", "Division by zero is undefined.")
                if op == "percent_change" and right.value < 0:
                    value = left.value - right.value
                    note = "Negative prior: report absolute change only; ordinary percentage growth is undefined by policy."
                else:
                    value = ((left.value - right.value) if op == "percent_change" else left.value) / right.value
                    unit, currency = "ratio", None
                    if op in {"percent_change", "ratio_percent"}:
                        value *= 100
                        unit = "percent"
            value = decimal(format(value, "f"))
            expression = f"{op}({left.expression}, {right.expression})"
            ids = tuple(dict.fromkeys(left.ids + right.ids))
            trace.append({"rule_id": op, "premises": list(ids), "outcome": "pass",
                          "normalized_inputs": [str(left.value), str(right.value)],
                          "result": format(value, "f"), "unit": unit, "note": note})
            return Quantity(value, unit, currency, left.issuer, left.scope, left.period,
                            tuple(sorted(left.metrics + right.metrics)), ids, expression)

        with localcontext() as ctx:
            ctx.prec = 28
            result = visit(plan["expression"])
        require(set(requested) == used, "requested_period", "A requested period was not used.")
        return {"status": "ok", "result": format(result.value, "f"), "unit": result.unit,
                "currency": result.currency, "expression": result.expression, "program": plan,
                "operand_ids": list(result.ids), "operands": operands, "rule_trace": trace,
                "decimal_precision": 28}
    except RuleFailure as exc:
        trace.append({"rule_id": exc.rule, "outcome": "fail", "reason": str(exc)})
        return {"status": "rule_failure", "error_code": exc.rule, "message": str(exc),
                "operands": operands, "rule_trace": trace}
    except (TypeError, KeyError, InvalidOperation, OverflowError, RecursionError):
        return {"status": "rule_failure", "error_code": "invalid_structure",
                "message": "Malformed calculation input.", "rule_trace": trace}
