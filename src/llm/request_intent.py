"""Reconcile explicit company/year words with selected source constraints before inference."""
import re


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
        aliases = {company, short, option.ticker}
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
