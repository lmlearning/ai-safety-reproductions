"""Dormant stdlib-only ROOT915 classifier. No model, array or native-process reader."""
import argparse
import datetime as dt
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

MODELS = ['r' + str(i) for i in range(1, 9)] + ['r_dyn']
COMMON_ORIGIN = '2026-10-15T13:28:33.952532+00:00'
COMMON_END = '2026-10-21T13:28:33.952532+00:00'
PANEL_BOUND = Fraction(1, 50)
MAX_BOUND = Fraction(1, 20)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pack(x):
    return {'numerator': x.numerator, 'denominator': x.denominator, 'decimal': float(x)}


def bins(intervals):
    require(type(intervals) is list and intervals, 'Missing compatible interval union')
    result = []
    for b in intervals:
        require(type(b) is dict, 'Interval object')
        lo, hi, d = b['lower_numerator'], b['upper_numerator'], b['denominator']
        require(all(type(x) is int for x in (lo, hi, d)), 'Exact finite integer interval operands')
        require(d == 256 and 0 <= lo < hi <= d and hi == lo + 1, 'Original LUT bin geometry')
        require(b['lower_inclusive'] is True and type(b['upper_inclusive']) is bool, 'Original boundary flags')
        result.append((Fraction(lo, d), Fraction(hi, d), b['upper_inclusive']))
    return result


def union_metrics(correct, total, intervals):
    require(type(correct) is int and type(total) is int and total == 750 and 0 <= correct <= total,
            'Required exact finite correct/750 count')
    p = Fraction(correct, total)
    parts = bins(intervals)
    distances = [max(lo - p, p - hi, Fraction(0)) for lo, hi, _ in parts]
    # Infimum distance is zero at an excluded endpoint, though strict membership can be false.
    strict = any(lo <= p and (p <= hi if closed else p < hi) for lo, hi, closed in parts)
    return p, min(distances), strict, [
        {'lower': pack(p - hi), 'upper': pack(p - lo),
         'lower_inclusive': closed, 'upper_inclusive': True}
        for lo, hi, closed in parts]


def panel_aggregate(distances):
    require(type(distances) is list and distances and all(type(d) is Fraction and d >= 0 for d in distances),
            'Complete finite exact distance vector')
    mean = sum(distances, Fraction(0)) / len(distances)
    maximum = max(distances)
    return mean, maximum, mean <= PANEL_BOUND


def counts_matrix(value):
    require(type(value) is list and len(value) == 40, 'All40 inference recurrences')
    for row in value:
        require(type(row) is list and len(row) == 39, 'All39 heldout hops')
        require(all(type(v) is int and 0 <= v <= 750 for v in row), 'Every finite integer counter/750')
    return value


def adaptive_counts(value):
    require(type(value) is list and len(value) == 39 and all(type(v) is int and 0 <= v <= 750 for v in value),
            'Complete39 adaptive counters/750')
    return value


def cell_key(row):
    m, h, r = row['model'], row['hop'], row['inference_recurrence']
    require(m in MODELS and type(h) is int and 2 <= h <= 40, 'Known model and source hop')
    require((type(r) is int and 1 <= r <= 40) or r == 'adaptive', 'Explicit recurrence identity')
    return m, h, r


def expected_panel_keys(model):
    if model == 'r_dyn':
        return {(model, h, r) for h in range(2, 41) for r in range(1, 25)} | {
            (model, h, 'adaptive') for h in range(2, 41)}
    return {(model, h, r) for h in range(2, 26) for r in range(1, 13)}


def audit_vectors(audit, full_ref):
    require(audit['schema'] == 'P157_COMPLETE_INDEPENDENT_WHOLE_DATA_LOGIT_COUNTER_AUDIT002', 'Original audit002 schema')
    require(audit['operational_audit_complete'] is True and audit['complete_full_ref'] == full_ref,
            'Whole independent audit and exact full product')
    require(audit['independent_full_neural_forward_rerun'] is False, 'Honest independent audit scope')
    require(type(audit['fixed']) is list and [r['model'] for r in audit['fixed']] == MODELS, 'All9 models exact order')
    matrices = {}
    for row in audit['fixed']:
        require(row['all40x29250_prediction_IDs_verified'] == 40 * 29250 and
                row['all_FP32_logit_elements_verified'] == 40 * 29250 * 217 and
                row['all_full_logits_finite'] is True, 'Complete every-example/vocabulary fixed audit')
        matrices[row['model']] = counts_matrix(row['complete_correct_counts'])
    require(type(audit['adaptive']) is list and len(audit['adaptive']) == 2, 'Both adaptive policies')
    adaptive = {}
    for row in audit['adaptive']:
        eps = row['eps_KL']
        require(type(eps) is float and eps in (.01, .001) and eps not in adaptive, 'Exact distinct original eps policies')
        require(row['examples_verified'] == 29250 and
                row['all_actual_decision_predicates_and_selected_full_logits_verified'] is True and
                row['no_independent_neural_forward_rerun_claim'] is True, 'Every original adaptive decision audited')
        adaptive[eps] = adaptive_counts(row['correct_integer_counts'])
    require(set(adaptive) == {.01, .001}, 'No sensitivity substitution')
    require(sum(len(r) for matrix in matrices.values() for r in matrix) == 14040, 'All14040 fixed cells')
    return matrices, adaptive


def evaluate(target, audit, comparison, full_ref):
    matrices, adaptive = audit_vectors(audit, full_ref)
    require(target['whole_cell_count'] == 3279 and target['unrecognized_source_pixels'] == [], 'Frozen complete source targets')
    require([p['model'] for p in target['panels']] == MODELS, 'All9 source panels in original order')
    require(comparison['published_cell_count'] == 3279 and len(comparison['all3279_records']) == 3279, 'All3279 comparison records')
    prior = {}
    for row in comparison['all3279_records']:
        key = cell_key(row)
        require(key not in prior, 'Duplicate comparison cell')
        prior[key] = row
    cells, panels, seen, strict_disagreements = [], [], set(), []
    for panel in target['panels']:
        model = panel['model']; expected = expected_panel_keys(model); observed = set(); distances = []
        require(panel['cell_count'] == len(expected) == len(panel['cells']), 'Whole source panel count')
        for source in panel['cells']:
            key = cell_key(source)
            require(key in expected and key not in observed and key not in seen, 'Complete unique original panel identity')
            observed.add(key); seen.add(key); m, h, r = key
            n = adaptive[.01][h - 2] if r == 'adaptive' else matrices[m][r - 1][h - 2]
            old = prior[key]
            require(type(old['correct']) is int and old['correct'] == n and type(old['total']) is int and old['total'] == 750,
                    'Published comparison joined to independently rebuilt exact counters')
            intervals = source['all_possible_accuracy_intervals']
            require(old['every_source_RGB_inverse_bin'] == intervals, 'Entire original interval union, no source reinterpretation')
            p, distance, strict, signed_union = union_metrics(n, 750, intervals)
            require(type(old['passed']) is bool, 'Typed retained strict diagnostic')
            if old['passed'] != strict:
                strict_disagreements.append({'model': m, 'hop': h, 'inference_recurrence': r,
                                             'retained': old['passed'], 'independently_recomputed': strict})
            distances.append(distance)
            cells.append({'model': m, 'hop': h, 'inference_recurrence': r, 'correct': n, 'total': 750,
                          'accuracy': pack(p), 'every_original_source_interval': intervals,
                          'distance_to_interval_union': pack(distance), 'signed_difference_compatible_union': signed_union,
                          'strict_RGB_membership_recomputed_diagnostic': strict, 'within_global_max_bound': distance <= MAX_BOUND})
        require(observed == expected, 'No missing source panel cell')
        mean, maximum, passed = panel_aggregate(distances)
        panels.append({'model': model, 'printed_ID_max_hop': panel['printed_ID_max_hop'], 'cells': len(distances),
                       'mean_distance': pack(mean), 'maximum_distance': pack(maximum), 'mean_bound': pack(PANEL_BOUND),
                       'mean_bound_passed': passed, 'full_cell_vector_indices': [i for i, x in enumerate(cells) if x['model'] == model]})
    require(len(cells) == len(seen) == len(prior) == 3279 and seen == set(prior), 'All3279, no omission or duplicate')
    maximum = max(Fraction(x['distance_to_interval_union']['numerator'], x['distance_to_interval_union']['denominator']) for x in cells)
    quantitative = all(p['mean_bound_passed'] for p in panels) and maximum <= MAX_BOUND
    return {'all3279_cells': cells, 'all9_panel_summaries': panels, 'global_max_distance': pack(maximum),
            'global_max_bound': pack(MAX_BOUND), 'quantitative_near_bounds_passed': quantitative,
            'all14040_audited_fixed_integer_counts': matrices,
            'both_adaptive_all39_audited_integer_counts': {'paper_0p01': adaptive[.01], 'source_0p001': adaptive[.001]},
            'retained_strict_AND_diagnostic': comparison['all_published_cells_AND'],
            'recomputed_strict_AND_diagnostic': all(x['strict_RGB_membership_recomputed_diagnostic'] for x in cells),
            'strict_diagnostic_disagreements': strict_disagreements,
            'strict_AND_is_not_a_near_veto': True}


def timestamp(s):
    require(type(s) is str, 'Explicit timestamp string')
    x = dt.datetime.fromisoformat(s)
    require(x.tzinfo is not None, 'UTC-aware clock')
    return x


def pin(path, deadline):
    p = Path(path); require(p.is_file() and not p.is_symlink(), 'Exact ordinary source/product file')
    before = p.stat(); digest = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            require(dt.datetime.now(dt.timezone.utc) < deadline, 'Original classification cutoff during custody')
            digest.update(block)
    after = p.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'File custody race')
    return {'path': str(p), 'bytes': after.st_size, 'sha256': digest.hexdigest()}


def read_ref(ref, deadline, parse=True):
    require(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}, 'Exact three-field reference')
    require(pin(ref['path'], deadline) == ref, 'Reference byte identity')
    if not parse:
        return None
    require(ref['bytes'] <= 32 * 1024**2, 'Bounded JSON metadata input; larger requires new source review')
    raw = Path(ref['path']).read_bytes()
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Parse-byte identity')
    def invalid_constant(_):
        raise ValueError('Nonfinite JSON is not a scientific value')
    return json.loads(raw, parse_constant=invalid_constant)


def validate_closure(closed, control, deadline):
    require(closed['schema'] == 'ROOT_P157_CLOSED_WHOLE_FAMILY_NEAR_INPUT_QUALIFICATION001', 'Explicit ROOT closed-input qualification')
    for key in ('ROOT_closed_full_and_whole_independent_audit_qualified', 'ROOT_exact_original_inputs_and_scope_verified',
                'ROOT_native_tool_handle_stream_and_clock_closure_qualified', 'ROOT_ordered_operational_violation_disposition_complete'):
        require(closed.get(key) is True, 'Unqualified ROOT custody/scope: ' + key)
    for k in ('complete_full_ref', 'whole_audit_ref', 'published_comparison_ref', 'source_target_ref', 'near_policy_ref',
              'same_original_common_grant_ref', 'original_audit_source_ref'):
        require(closed[k] == control[k], 'Exact qualified input join: ' + k)
    require(closed['original_common_origin_UTC'] == COMMON_ORIGIN and closed['original_common_deadline_UTC'] == COMMON_END,
            'No changed original programme clock')
    require(closed['whole_scope'] == {'models': MODELS, 'heldout_examples': 29250, 'hops': list(range(2, 41)),
            'examples_per_hop': 750, 'fixed_inference_recurrences': list(range(1, 41)),
            'fixed_accuracy_counters': 14040, 'published_targets': 3279, 'adaptive_eps_KL': [.01, .001]},
            'Explicit complete original family; no partial checkpoint or adaptive substitution')
    require(closed['unresolved_material_operational_violations'] == [], 'Unresolved material operational evidence')
    events = closed['ordered_operational_violation_dispositions']
    require(type(events) is list, 'Ordered explicit violation ledger, empty only if no violations')
    for i, event in enumerate(events):
        require(event['ordinal'] == i + 1 and event['ROOT_disposition_complete'] is True and event['material_impact_resolved'] is True,
                'Every operational event retains an accepted finite disposition')
        require(type(event['description']) is str and event['description'] and event['evidence_refs'], 'Raw evidence for violation')
        for r in event['evidence_refs']:
            read_ref(r, deadline, False)
    require(set(closed['phases']) == {'full', 'independent_audit'}, 'Both actual phases, no P0197182-case confusion')
    for phase in closed['phases'].values():
        require(phase['ROOT_actual_closure_accepted'] is True and phase['retained_handles_closed'] is True and
                phase['streams_closed'] is True and phase['effective_operational_pass'] is True,
                'Native/tool/direct retained custody must be qualified')
        for field in ('actual_tool_chain_ref', 'native_parent_terminal_ref'):
            read_ref(phase[field], deadline, False)
        require(type(phase['actual_tool_exit']) is int and type(phase['actual_child_native_exit']) is int,
                'Actual exit codes, no inferred native exit')
        require(phase['actual_child_native_exit'] != 259, 'Source native STILL_ACTIVE cannot qualify closed phase')
        if phase['actual_tool_exit'] != 0 or phase['actual_child_native_exit'] != 0:
            require(phase['nonzero_exit_disposition_ordinals'] and all(type(i) is int and 1 <= i <= len(events)
                    for i in phase['nonzero_exit_disposition_ordinals']), 'Nonzero needs ordered ROOT disposition, never silent pass')
        require(type(phase['Job_enforcement_claimed']) is bool, 'Explicit native scope')
        if phase['Job_enforcement_claimed']:
            require(phase['Job_final_active'] == 0 and phase['Job_handle_closed'] is True, 'Claimed Job final closure')
        else:
            require(phase['Job_final_active'] is None and phase['Job_handle_closed'] is None, 'Do not invent Job evidence')


def claim_status(ref, control, policy, deadline):
    if ref is None:
        return 'UNKNOWN', [{'id': c['id'], 'status': 'UNKNOWN', 'source_role_verbatim': c} for c in policy['P157_fixed_substantive_claim_roles']]
    doc = read_ref(ref, deadline)
    require(doc['ROOT_complete_C1_C4_source_bound_review_accepted'] is True, 'Explicit ROOT substantive review')
    for k in ('complete_full_ref', 'whole_audit_ref', 'published_comparison_ref', 'source_target_ref', 'near_policy_ref'):
        require(doc[k] == control[k], 'Claim source/product join: ' + k)
    require([c['id'] for c in doc['claims']] == ['C1', 'C2', 'C3', 'C4'], 'Exactly fixed original Figure5 C1-C4 roles')
    for role, row in zip(policy['P157_fixed_substantive_claim_roles'], doc['claims']):
        require(row['source_role_verbatim'] == role and row['status'] in ('COMPATIBLE', 'MATERIAL_REVERSAL', 'UNKNOWN'), 'No new scientific role')
        require(type(row['source_bound_reason']) is str and row['source_bound_reason'], 'Source-bound reason, not a bare flag')
    statuses = [r['status'] for r in doc['claims']]
    return ('MATERIAL_REVERSAL' if 'MATERIAL_REVERSAL' in statuses else 'UNKNOWN' if 'UNKNOWN' in statuses else 'COMPATIBLE'), doc['claims']


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--control', required=True); args = parser.parse_args()
    control = json.loads(Path(args.control).read_bytes())
    for key in ('execution_authorized', 'ROOT_classifier_source_review_accepted', 'ROOT_closed_products_admitted', 'ROOT_classification_phase_admitted'):
        require(control.get(key) is True, 'Dormant control: ' + key)
    deadline = timestamp(control['absolute_work_cutoff_UTC'])
    require(timestamp(COMMON_ORIGIN) <= dt.datetime.now(dt.timezone.utc) < deadline <= timestamp(COMMON_END), 'Same unreset original clock')
    packet = read_ref(control['current_source_packet_ref'], deadline)
    require(packet['actor_ref'] == pin(__file__, deadline), 'Frozen current classifier source')
    review = read_ref(control['ROOT_classifier_source_review_ref'], deadline)
    require(review['ROOT_P157_closed_near_classifier_source_accepted'] is True and
            review['current_source_packet_ref'] == control['current_source_packet_ref'], 'Exact ROOT source acceptance')
    for k in ('near_policy_ref', 'source_target_ref', 'same_original_common_grant_ref', 'original_audit_source_ref'):
        require(packet[k] == control[k], 'Frozen source method: ' + k)
    read_ref(control['original_audit_source_ref'], deadline, False)
    grant = read_ref(control['same_original_common_grant_ref'], deadline)
    require(grant['schema'] == 'P157_ONE_144H_PROGRAMME_GRANT001' and grant['execution_authorized'] is True and
            grant['common_origin_UTC'] == COMMON_ORIGIN and grant['common_deadline_UTC'] == COMMON_END and
            grant['total_seconds'] == 518400, 'Exact original programme authority, no reset or added allowance')
    policy = read_ref(control['near_policy_ref'], deadline)
    require(policy['ROOT_policy_adopted'] is True and policy['operative_numeric_bounds']['P157'] == packet['operative_numeric_bounds'], 'Original915 exact bound specification')
    closed = read_ref(control['ROOT_closed_whole_scope_and_custody_ref'], deadline)
    validate_closure(closed, control, deadline)
    # Full manifest is opaque here; audit002 independently rebuilt all required count vectors from every original array.
    read_ref(control['complete_full_ref'], deadline, False)
    result = evaluate(read_ref(control['source_target_ref'], deadline), read_ref(control['whole_audit_ref'], deadline),
                      read_ref(control['published_comparison_ref'], deadline), control['complete_full_ref'])
    status, claims = claim_status(control['ROOT_C1_C4_compatibility_ref'], control, policy, deadline)
    result.update(schema='P157_COMPLETE_CLOSED_NEAR_BOUND_CLASSIFICATION001', substantive_claim_status=status,
                  fixed_C1_C4_source_roles_and_dispositions=claims, all_source_role_wording_ref=control['near_policy_ref'],
                  near_success_candidate=result['quantitative_near_bounds_passed'] and status == 'COMPATIBLE',
                  classification=('OUTSIDE_FIXED_NEAR_BOUND' if not result['quantitative_near_bounds_passed'] else
                                  'NOT_NEAR_MATERIAL_REVERSAL' if status == 'MATERIAL_REVERSAL' else
                                  'QUANTITATIVE_NEAR_PENDING_ROOT_C1_C4' if status == 'UNKNOWN' else 'NEAR_SUCCESS_CANDIDATE'),
                  ROOT_final_counting_required=True, paper_credit=0, all_inputs={k: control[k] for k in
                  ('complete_full_ref', 'whole_audit_ref', 'published_comparison_ref', 'source_target_ref', 'near_policy_ref',
                   'ROOT_closed_whole_scope_and_custody_ref', 'ROOT_C1_C4_compatibility_ref')})
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'Original cutoff after full classification')
    out = Path(control['exclusive_output_directory']).absolute()
    base = Path(packet['allowed_output_parent']).absolute()
    require(out.parent == base and not out.exists() and base.is_dir(), 'One new direct child under original science14GiB pool')
    raw = (json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(',', ':')) + '\n').encode('ascii')
    require(len(raw) <= 16 * 1024**2, 'Bounded full unthinned classifier result')
    out.mkdir()
    p = out / 'COMPLETE_ALL3279_ALL14040_NEAR_BOUND_CANDIDATE001.json'
    with p.open('xb') as stream:
        require(stream.write(raw) == len(raw), 'Complete exclusive full-vector output')
    output_ref = pin(p, deadline)
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'Original cutoff after actual write/hash')
    print(json.dumps({'operational_complete': True, 'output_ref': output_ref, 'paper_credit': 0,
                      'claim_status': status, 'classification': result['classification']}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
