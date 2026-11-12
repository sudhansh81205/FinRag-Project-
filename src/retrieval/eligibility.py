"""One typed request-scope policy shared by dense and lexical retrieval.

Constructor filters are a ceiling: a request can narrow that scope, never widen it.
This is a KR integrity predicate common to every experimental variant, not the
separate hierarchical candidate restriction introduced at stage E.
"""

from copy import deepcopy

FILTER_KEYS = frozenset({
    "ticker", "accession", "section", "period_end", "period_start",
    "fiscal_year", "scope", "normalized_unit",
})


def validated_filters(filters=None):
    if filters is None:
        return {}
    if not isinstance(filters, dict):
        raise ValueError("Eligibility filters must be a dictionary")
    if "type" in filters:
        raise ValueError("Use stream limits for the record type filter")
    if set(filters) - FILTER_KEYS:
        raise ValueError("Unsupported eligibility filter")
    for value in filters.values():
        values = value if isinstance(value, list) else [value]
        if not all(type(v) in (str, int) and (not isinstance(v, str) or bool(v.strip()))
                   for v in values):
            raise ValueError("Invalid eligibility filter value")
    return deepcopy(filters)


def intersect_filters(*scopes):
    """Intersect scalar/list equality predicates without modifying any caller."""
    combined = {}
    for scope in scopes:
        for key, value in validated_filters(scope).items():
            if key not in combined:
                combined[key] = value
                continue
            previous = combined[key]
            old = previous if isinstance(previous, list) else [previous]
            new = value if isinstance(value, list) else [value]
            # Keep original order, and retain an empty intersection as [] (match none).
            combined[key] = [v for v in old if v in new]
    return combined


def eligible(record, filters):
    metadata = record.get("metadata", {})
    return all(metadata.get(key) in value if isinstance(value, list)
               else metadata.get(key) == value for key, value in filters.items())


def empty_scope(filters):
    return any(isinstance(value, list) and not value for value in filters.values())
