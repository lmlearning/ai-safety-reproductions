"""Mechanical published-cell reporting; no auxiliary all-target veto or paper credit."""
from decimal import Decimal


def add_derivatives(facts):
    attrs = ('Guidance', 'Informativeness', 'Relevance', 'Safety', 'Empathy', 'Helpfulness', 'Understanding')
    models = ('claude', 'ds_llama', 'ds_qwen', 'gemini', 'gpt4o', 'gpt4omini', 'llama_3', 'qwen_2', 'qwen_3')
    judges = ('Claude', 'GPT-4o', 'Gemini', 'o4-mini')
    def mean(xs):
        return None if any(x is None for x in xs) else sum(xs) / len(xs)
    human = {m: mean([facts['human_all_valid_model_means'][m][a]['mean'] for a in attrs]) for m in models}
    jm = {j: {m: mean([facts['judge_all_valid_model_means'][j][m][a] for a in attrs]) for m in models} for j in judges}
    overall = {m: mean([jm[j][m] for j in judges]) for m in models}
    def ranks(d):
        return {m: None if d[m] is None or any(v is None for v in d.values()) else 1 + sum(v > d[m] for v in d.values()) for m in models}
    facts['display_derivatives'] = {'human_model_average': human, 'judge_model_average': jm,
                                   'judge_model_rank': {j: ranks(jm[j]) for j in judges},
                                   'all_judge_average': overall, 'all_judge_rank': ranks(overall),
                                   'rank_rule': 'competition rank; ties retained; auxiliary only',
                                   'auxiliary_judge_mean_rule': 'all valid judge ratings; historical weighting not independently established'}


def lookup(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def compare_all(facts, bindings):
    """All 1150 source targets emitted; ambiguous labels remain UNKNOWN explicitly."""
    add_derivatives(facts)
    rows = []
    for b in bindings['bindings']:
        path = b.get('metric_path')
        actual = lookup(facts, path) if path is not None else None
        expected = Decimal(b['published_numeric_lexeme'])
        delta = None if actual is None else abs(Decimal(str(actual)) - expected)
        halfunit = Decimal(5).scaleb(-int(b['display_decimal_places']) - 1)
        tolerance = b.get('proposed_primary_NEAR_abs_bound')
        rows.append({**b, 'actual': actual, 'absolute_error': None if delta is None else str(delta),
                     'within_published_display_halfunit': None if delta is None else delta <= halfunit,
                     'proposed_NEAR_numeric_pass': None if tolerance is None or delta is None else delta <= Decimal(str(tolerance)),
                     'status': 'UNKNOWN_SOURCE_LABEL_OR_AGGREGATION' if actual is None else 'COMPUTED_DIAGNOSTIC'})
    if len(rows) != 1150:
        raise ValueError('Every original published numeric target must be reported')
    primary = [r for r in rows if r['published_table'] in (2, 3, 4)]
    if len(primary) != 324:
        raise ValueError('Complete main Tables2-4 family required')
    return {'schema': 'MENTALBENCH_ALL1150_PUBLISHED_TARGET_REPORT001', 'all1150': rows,
            'main324_proposed_numeric_bound_conjunction': all(r['proposed_NEAR_numeric_pass'] is True for r in primary),
            'auxiliary_all_exact_conjunction_used_for_NEAR': False,
            'scientific_counting_authority': False,
            'independent_audit_required': True}
