"""Dormant original-source statistical core. No I/O, imports of NumPy, or execution on import.

NumPy is supplied only by an independently qualified future caller. Source lineage:
MentalBench Oct21 commit 7074d5cea423799171ce7d7125684af9ccd211f0,
icc_corrected_with_bootstrap_ci.py and calculate_real_mse_rmse.py.
This is new source, not an execution of the author implementation.
"""
import math

ATTRIBUTES = ('Guidance', 'Informativeness', 'Relevance', 'Safety',
              'Empathy', 'Helpfulness', 'Understanding')
MODELS = ('claude', 'ds_llama', 'ds_qwen', 'gemini', 'gpt4o', 'gpt4omini',
          'llama_3', 'qwen_2', 'qwen_3', 'human')
AI_MODELS = MODELS[:-1]
JUDGES = ('Claude', 'GPT-4o', 'Gemini', 'o4-mini')
EXCLUDE = {'Claude': 'claude', 'GPT-4o': 'gpt4o',
           'Gemini': 'gemini', 'o4-mini': 'gpt4omini'}
OPEN_MODELS = ('ds_llama', 'ds_qwen', 'llama_3', 'qwen_2', 'qwen_3')


def primitive(x):
    """Strict JSON primitive conversion: undefined numeric quantities remain null."""
    if x is None or isinstance(x, (str, bool, int)):
        return x
    if isinstance(x, dict):
        return {str(k): primitive(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [primitive(v) for v in x]
    v = float(x)
    return v if math.isfinite(v) else None


def anova_icc(h, l, np):
    if len(h) != len(l) or len(h) < 2:
        raise ValueError('ICC requires the complete paired model family')
    y = np.column_stack([np.asarray(h, dtype=float), np.asarray(l, dtype=float)])
    n, k = y.shape
    grand = float(np.mean(y))
    sr = k * float(np.sum((np.mean(y, axis=1) - grand) ** 2))
    sc = n * float(np.sum((np.mean(y, axis=0) - grand) ** 2))
    st = float(np.sum((y - grand) ** 2))
    msr, msc, mse = sr / (n - 1), sc / (k - 1), (st - sr - sc) / ((n - 1) * (k - 1))
    d1 = msr + (k - 1) * mse
    d2 = d1 + k * (msc - mse) / n
    return {'icc_c1': (msr - mse) / d1 if d1 != 0 else float('nan'),
            'icc_a1': (msr - mse) / d2 if d2 != 0 else float('nan'),
            'msr': msr, 'msc': msc, 'anova_mse': mse, 'n_models': n}


def bootstrap(h, l, np, guard):
    """Serial source bootstrap; retains all draws, including author-filtered draws.

    Source bootstrap_icc_sample jointly returns NaN/NaN when either ICC is NaN.
    The parent subsequently filters finite [0,1] C1/A1 independently. This two-step
    rule is retained; it is not a claim of unconditional 95% interval coverage.
    """
    np.random.seed(42)
    seeds = np.random.randint(0, 100000, 1000)
    h, l = np.asarray(h, dtype=float), np.asarray(l, dtype=float)
    raw_c, raw_a, indices, joint_mask, c_mask, a_mask = [], [], [], [], [], []
    c1, a1 = [], []
    for ordinal, seed in enumerate(seeds):
        if ordinal % 25 == 0:
            guard()
        np.random.seed(int(seed))
        ix = np.random.choice(len(h), size=len(h), replace=True)
        r = anova_icc(h[ix], l[ix], np)
        c, a = float(r['icc_c1']), float(r['icc_a1'])
        joint_nan = bool(np.isnan(c) or np.isnan(a))
        if joint_nan:
            c, a = float('nan'), float('nan')
        vc = math.isfinite(c) and 0 <= c <= 1
        va = math.isfinite(a) and 0 <= a <= 1
        if vc:
            c1.append(c)
        if va:
            a1.append(a)
        indices.append([int(i) for i in ix])
        raw_c.append(primitive(c))
        raw_a.append(primitive(a))
        joint_mask.append(joint_nan)
        c_mask.append(vc)
        a_mask.append(va)
    alpha = 1 - 0.95
    def summary(v):
        return {'valid': len(v), 'discarded': 1000 - len(v),
                'lower': float(np.percentile(v, 100 * alpha / 2)) if len(v) >= 10 else None,
                'upper': float(np.percentile(v, 100 * (1 - alpha / 2))) if len(v) >= 10 else None,
                'mean': float(np.mean(v)) if v else None,
                'std_ddof0': float(np.std(v)) if v else None}
    return {'c1': summary(c1), 'a1': summary(a1), 'source_n_valid_samples': min(len(c1), len(a1)),
            'all_1000_raw_c1': raw_c, 'all_1000_raw_a1': raw_a,
            'joint_nan_mask_hex_little_endian': np.packbits(joint_mask, bitorder='little').tobytes().hex(),
            'c1_author_filter_mask_hex_little_endian': np.packbits(c_mask, bitorder='little').tobytes().hex(),
            'a1_author_filter_mask_hex_little_endian': np.packbits(a_mask, bitorder='little').tobytes().hex(),
            'seed_index_design': {'all1000_integer_seeds': [int(s) for s in seeds],
                                  'all1000_model_index_draws': indices,
                                  'model_index_base': 0}}


def paired_metrics(h, l, np):
    h, l = np.asarray(h, dtype=float), np.asarray(l, dtype=float)
    if len(h) != len(l) or len(h) < 2:
        raise ValueError('Missing complete paired-error family')
    d = l - h
    hm, lm = float(np.mean(h)), float(np.mean(l))
    hs, ls = float(np.std(h, ddof=1)), float(np.std(l, ddof=1))
    cov = float(np.sum((h - hm) * (l - lm)) / (len(h) - 1))
    rho = cov / (hs * ls) if hs != 0 and ls != 0 else float('nan')
    den = hs * hs + ls * ls + (hm - lm) ** 2
    ccc = 2 * rho * hs * ls / den if den != 0 and math.isfinite(rho) else float('nan')
    bias, sd = float(np.mean(d)), float(np.std(d, ddof=1))
    return primitive({'n_pairs': len(h), 'human_mean': hm, 'llm_mean': lm,
                      'bias': float(np.mean(d)), 'mse': float(np.mean(d ** 2)),
                      'rmse': float(np.sqrt(np.mean(d ** 2))),
                      'human_std': hs, 'llm_std': ls, 'pearson_r': rho,
                      'lins_ccc': ccc, 'scale_shift': ls / hs if hs != 0 else None,
                      'bland_altman_mean_difference': bias,
                      'bland_altman_difference_sd_ddof1': sd,
                      'bland_altman_lower_LoA': bias - 1.96 * sd,
                      'bland_altman_upper_LoA': bias + 1.96 * sd,
                      'bland_altman_bias_SE': sd / math.sqrt(len(d)),
                      'bland_altman_LoA_SE': sd * math.sqrt(3 / len(d))})


def reduce_complete(values, np, guard):
    """values[judge][model][attribute] = {'human':1000 doubles,'judge':1000 doubles}.

    Complete released-record coverage is required outside this core. Original
    unparseable cells remain NaN with full denominators/masks; no imputation.
    All ten response sources exist, including original-human response source.
    ICC excludes exactly ONE response source per judge; includes human response.
    """
    if tuple(values) != JUDGES:
        raise ValueError('All four judges in fixed source order are required')
    model_means, cells, human_means, judge_model_means = {}, {}, {}, {}
    reference, bootstrap_design = None, None
    for judge in JUDGES:
        guard()
        if tuple(values[judge]) != MODELS:
            raise ValueError('All ten original response sources are required')
        model_means[judge], judge_model_means[judge] = {}, {}
        reference_now = []
        for model in MODELS:
            if tuple(values[judge][model]) != ATTRIBUTES:
                raise ValueError('All seven attributes are required')
            model_means[judge][model], judge_model_means[judge][model] = {}, {}
            for attr in ATTRIBUTES:
                h = np.asarray(values[judge][model][attr]['human'], dtype=float)
                l = np.asarray(values[judge][model][attr]['judge'], dtype=float)
                if h.shape != (1000,) or l.shape != (1000,):
                    raise ValueError('Full original 1000-record cohort required')
                if np.any(np.isinf(h)) or np.any(np.isinf(l)):
                    raise ValueError('Nonfinite nonmissing rating requires source disposition')
                mask = ~(np.isnan(h) | np.isnan(l))
                if not np.any(mask):
                    raise ValueError('Required model-attribute has no paired ratings')
                model_means[judge][model][attr] = {
                    'human': float(np.mean(h[mask])), 'judge': float(np.mean(l[mask])),
                    'paired_valid_n': int(np.sum(mask)), 'full_original_n': 1000}
                jvalid = ~np.isnan(l)
                judge_model_means[judge][model][attr] = float(np.mean(l[jvalid])) if np.any(jvalid) else None
                reference_now.append(h)
                if judge == JUDGES[0]:
                    hv = ~np.isnan(h)
                    human_means.setdefault(model, {})[attr] = {
                        'mean': float(np.mean(h[hv])) if np.any(hv) else None,
                        'valid_n': int(np.sum(hv)), 'full_original_n': 1000}
        if reference is None:
            reference = reference_now
        elif not all(np.array_equal(a, b, equal_nan=True) for a, b in zip(reference, reference_now)):
            raise ValueError('Released human reference differs across judge banks')
        cells[judge] = {}
        included = [m for m in MODELS if m != EXCLUDE[judge]]
        for attr in ATTRIBUTES:
            guard()
            hm = [model_means[judge][m][attr]['human'] for m in included]
            lm = [model_means[judge][m][attr]['judge'] for m in included]
            icc = anova_icc(hm, lm, np)
            boot = bootstrap(hm, lm, np, guard)
            design = boot.pop('seed_index_design')
            if bootstrap_design is None:
                bootstrap_design = design
            elif design != bootstrap_design:
                raise ValueError('Source-reused bootstrap design differs across cells')
            hp, lp = [], []
            masks = {}
            for model in included:
                h = np.asarray(values[judge][model][attr]['human'], dtype=float)
                l = np.asarray(values[judge][model][attr]['judge'], dtype=float)
                mask = ~(np.isnan(h) | np.isnan(l))
                hp.extend(h[mask].tolist())
                lp.extend(l[mask].tolist())
                masks[model] = np.packbits(mask, bitorder='little').tobytes().hex()
            p = paired_metrics(hp, lp, np)
            width = (boot['c1']['upper'] - boot['c1']['lower']) if boot['c1']['lower'] is not None else None
            bias = float(np.mean(np.asarray(lm) - np.asarray(hm)))
            cells[judge][attr] = primitive({**icc, 'included_models': included,
                'excluded_model': EXCLUDE[judge], 'equal_weight_human_mean': float(np.mean(hm)),
                'equal_weight_llm_mean': float(np.mean(lm)), 'equal_weight_bias': bias,
                'normalized_abs_equal_weight_bias': abs(bias) / 4,
                'paired_error': p, 'bootstrap': boot, 'c1_ci_width': width,
                'width_status': None if width is None else 'GR' if width <= .355 else 'MR' if width <= .560 else 'PR',
                'paired_masks_hex_little_endian': masks})
    return primitive({'schema': 'MENTALBENCH_COMPLETE_PRIMARY_FACTS001',
                      'all28_cells': cells, 'all_model_paired_means': model_means,
                      'human_all_valid_model_means': human_means,
                      'judge_all_valid_model_means': judge_model_means,
                      'shared_bootstrap_seed_index_design': bootstrap_design,
                      'actual_3_individual_raters_claimed': False,
                      'complete_CENTRAL_status': 'PENDING_INDEPENDENT_AUDIT_AND_ROOT',
                      'paper_credit': False})


def proposed_core_directions(facts):
    """921 contrasts; nominal boundary flags alone are not counting vetoes.

    Historical function name 'proposed' is retained. Fixed source contrasts are
    reported with propagated adopted small-error allowances, not changed by data.
    Independent audit/ROOT interprets compatibility versus material reversal.
    """
    def avg(xs):
        if any(x is None for x in xs):
            return None
        return sum(xs) / len(xs)
    def threshold(value, minimum, propagation):
        return {'value': value, 'source921_nominal_minimum': minimum,
                'nominal_pass': None if value is None else value >= minimum,
                'adopted_error_propagation_max': propagation,
                'within_propagated_small_error_of_nominal': None if value is None else value >= minimum - propagation,
                'nominal_boundary_failure_is_not_automatic_NEAR_failure': True}
    human = facts['human_all_valid_model_means']
    means = {m: avg([human[m][a]['mean'] for a in ATTRIBUTES]) for m in AI_MODELS}
    closed = [m for m in AI_MODELS if m not in OPEN_MODELS]
    out = {'method_status': 'SOURCE921_WITH_PROPAGATED_SMALL_ERROR_INTERPRETATION', 'per_judge': {}, 'scientific_credit': False}
    out['best_closed_minus_best_open'] = threshold(max(means[m] for m in closed) - max(means[m] for m in OPEN_MODELS), .10, .10)
    out['llama_minus_best_other_open'] = threshold(means['llama_3'] - max(means[m] for m in OPEN_MODELS if m != 'llama_3'), .15, .10)
    out['qwen3_lowest'] = {'nominal_pass': means['qwen_3'] <= min(means.values()), 'means': means,
                          'within_propagated_small_error': means['qwen_3'] <= min(means.values()) + .10,
                          'near_tie_not_automatic_failure': True}
    for j in JUDGES:
        c = facts['all28_cells'][j]
        cognitive = avg([c[a]['icc_c1'] for a in ('Guidance', 'Informativeness')])
        safety = avg([c[a]['icc_c1'] for a in ('Relevance', 'Safety')])
        cw = avg([c[a]['c1_ci_width'] for a in ('Guidance', 'Informativeness')])
        sw = avg([c[a]['c1_ci_width'] for a in ('Relevance', 'Safety')])
        out['per_judge'][j] = {
            'cognitive_minus_safety_C1': threshold(None if cognitive is None or safety is None else cognitive - safety, .10, .06),
            'empathy_C1_minus_A1': threshold(None if c['Empathy']['icc_c1'] is None or c['Empathy']['icc_a1'] is None else c['Empathy']['icc_c1'] - c['Empathy']['icc_a1'], .20, .06),
            'safety_minus_cognitive_width': threshold(None if sw is None or cw is None else sw - cw, .15, .14),
            'empathy_paired_bias': threshold(c['Empathy']['paired_error']['bias'], .40, .05),
            'helpfulness_paired_bias': threshold(c['Helpfulness']['paired_error']['bias'], .30, .05)}
    return out
