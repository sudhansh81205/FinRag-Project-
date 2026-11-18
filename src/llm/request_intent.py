"""Reconcile explicit company/year words with selected source constraints before inference."""
import re
from datetime import date

_COMPANY_ALIASES = {"CSCO": ("Cisco",)}


def named_years(question):
    years = {int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b', question)}
    years.update(int(y) for y in re.findall(r'\bfy\s*((?:19|20)\d{2})\b', question, re.I))
    years.update(2000 + int(y) for y in re.findall(r"\bfy\s*'?([0-9]{2})\b", question, re.I))
    return sorted(years)


def company_conflict(question, selected, options):
    mentions = set()
    for option in options:
        company = option.company if hasattr(option, 'company') else option.issuer
        short = re.sub(r'\s+(?:inc\.?|corporation|corp\.?)$', '', company, flags=re.I)
        aliases = {company, short, option.ticker, *_COMPANY_ALIASES.get(option.ticker, ())}
        if any(re.search(r'(?<!\w)' + re.escape(a) + r'(?!\w)', question, re.I) for a in aliases):
            mentions.add(option.ticker)
    # Catch explicit names outside the inventory, rather than silently using the selection.
    candidates = re.findall(r"\b([A-Za-z][A-Za-z0-9.-]*(?:\s+(?:Inc|Corp|Corporation|Ltd)\.?)?)['’]s\s+(?:gross|net|total|operating|revenue|assets|liabilities|cash|equity)", question, re.I)
    candidates += re.findall(r"\b(?:did|does)\s+([A-Za-z][A-Za-z0-9.-]*(?:\s+(?:Inc|Corp|Corporation|Ltd)\.?)?)\s+(?:report|describe|earn|generate|have)", question, re.I)
    candidates += re.findall(r"\bwhat\s+(?:was|were|is|are)\s+([A-Za-z][A-Za-z0-9.-]*)\s+(?:revenue|gross margin|net income|operating income|earnings)", question, re.I)
    candidates += re.findall(r"\bcompare\s+([A-Za-z][A-Za-z0-9.-]*)\s+(?:and|versus|vs|with)\b", question, re.I)
    def normalize(value):
        return re.sub(r'[^a-z0-9]', '', value.lower())
    selected_names = {normalize(selected.company), normalize(selected.ticker), normalize(re.sub(r'\s+(?:inc\.?|corporation|corp\.?)$', '', selected.company, flags=re.I))}
    selected_names.update(normalize(alias) for alias in _COMPANY_ALIASES.get(selected.ticker, ()))
    generic = {'the', 'total', 'annual', 'consolidated', 'reported'}
    if any(normalize(name) not in selected_names and name.lower() not in generic for name in candidates):
        return 'The company named in your question does not match the selection. Choose a supported company and use matching filing evidence.'
    if mentions - {selected.ticker}:
        return f'The question names a different company. Select the matching company and filing before asking; current selection is {selected.company}.'
    return ''


def requested_periods(question, request, records, period_kind):
    """Source-derived boundaries for one year or two adjacent comparison years."""
    if re.search(r'\b(?:q[1-4]|quarter(?:ly)?|today|current stock price|forecast|predict)\b', question, re.I):
        return None, 'This workspace uses annual filing evidence. Quarterly values, live prices and predictions require a different source.'
    years = named_years(question)
    comparison = bool(re.search(r'\b(change|growth|increase|decrease|difference|compare|compared|versus|vs)\b', question, re.I))
    selected_year = int(request.value_period_end[:4])
    if len(years) > 2 or len(years) == 2 and not comparison:
        return None, 'Choose a single value year, or ask an explicit comparison between two adjacent fiscal years.'
    if years and max(years) != selected_year:
        return None, f'The question asks for {max(years)}, but the selected value period ends {request.value_period_end}. Change the value period or question.'
    if len(years) == 2 and years[1] != years[0] + 1:
        return None, 'Annual comparisons require two adjacent fiscal years.'
    if comparison and len(years) != 2:
        return None, 'Name both fiscal years for a comparison, for example FY2020 to FY2021.'
    target_years = years or [selected_year]
    found = set()
    for record in records:
        m = record.get('metadata', {})
        if (m.get('accession') == request.accession and m.get('type') == 'table_cell'
                and m.get('scope') == request.scope and m.get('period_kind') == period_kind
                and str(m.get('period_end', ''))[:4] in {str(y) for y in target_years}):
            found.add((m.get('period_kind'), m.get('period_start'), m.get('period_end')))
    if len(found) != len(target_years) or {int(p[2][:4]) for p in found} != set(target_years):
        return None, 'The selected filing does not contain unambiguous typed source periods for all requested years.'
    if max(p[2] for p in found) != request.value_period_end:
        return None, 'The selected value-period end does not match the actual source boundary.'
    return [{'kind': k, 'start': s, 'end': e} for k, s, e in sorted(found, key=lambda p: p[2])], ''

_COUNT_WORDING = re.compile(r"\b(?:how many|(?:total )?number of|count|headcount)\b", re.I)
_HEADCOUNT_TERMS = re.compile(r"\b(?:employees?|headcount|workforce)\b", re.I)
_MONTH = r"January|February|March|April|May|June|July|August|September|October|November|December"
_CALENDAR_DATE = re.compile(
    rf"\b(?P<month>{_MONTH})(?:\s+(?P<day>\d{{1,2}}),?)?\s+(?P<year>\d{{4}})\b"
    r"|\b(?P<iso>\d{4}-\d{2}-\d{2})\b", re.I,
)
_HEADCOUNT_WORDS = frozenset("""
    a an as at by cite company count did does employee employees end fiscal for
    give global had has have headcount how in is it many me of on please report
    reported s source tell the total was were what workforce worldwide year number
    and with provide size
""".split())


def asks_for_count(question):
    return bool(_COUNT_WORDING.search(question))


def asks_for_headcount(question):
    return bool(_HEADCOUNT_TERMS.search(question)) and (
        asks_for_count(question)
        or bool(re.search(r"\b(?:total employees|employee headcount|workforce size)\b", question, re.I))
    )


def headcount_scope_matches(question, request):
    """Accept only a whole-company headcount at the filing's selected end date."""
    if request.scope != "consolidated" or request.value_period_end != request.filing_period_end:
        return False
    end = date.fromisoformat(request.value_period_end)
    if named_years(question) not in ([], [end.year]):
        return False
    for match in _CALENDAR_DATE.finditer(question):
        if match["iso"]:
            if match["iso"] != request.value_period_end:
                return False
        elif (match["month"].casefold() != end.strftime("%B").casefold()
              or int(match["year"]) != end.year
              or (match["day"] and int(match["day"]) != end.day)):
            return False
    question = _CALENDAR_DATE.sub("", question)
    question = re.sub(r"\b(?:fy\s*'?\s*)?(?:19|20)\d{2}\b", "", question, flags=re.I)
    company = re.sub(r"[,\s]+(?:Inc\.?|Corporation|Corp\.?)$", "", request.company, flags=re.I)
    names = [request.company, company, request.ticker, *_COMPANY_ALIASES.get(request.ticker, ())]
    for name in sorted(names, key=len, reverse=True):
        question = re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)", "", question, flags=re.I)
    return set(re.findall(r"\w+", question.lower())) <= _HEADCOUNT_WORDS
