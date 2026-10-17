"""Dormant streaming CSV adapter using an exterior ROOT-qualified original map.

The map is NOT available or qualified in this packet. No row-position identity,
unknown header alias, source-rater aggregation, or raw-workbook join is invented.
"""
import array
import csv
import hashlib
import json
import math

ATTRIBUTES = ('Guidance', 'Informativeness', 'Relevance', 'Safety', 'Empathy', 'Helpfulness', 'Understanding')
MODELS = ('claude', 'ds_llama', 'ds_qwen', 'gemini', 'gpt4o', 'gpt4omini', 'llama_3', 'qwen_2', 'qwen_3', 'human')
JUDGES = ('Claude', 'GPT-4o', 'Gemini', 'o4-mini')


def rating(text, attr):
    """Original source parser, with explicit reasons and no fuzzy repair/clipping.

    CSV empty strings/declared source NA lexical tokens are normalized outside.
    Boolean float coercion follows author float(val), and is separately flagged.
    Finite values outside the intended 1..5 scale are retained and flagged, as author float; no clipping or implicit new veto.
    """
    if text == '':
        return float('nan'), 'empty_source_cell'
    s = text.strip()
    if s.startswith('```json'):
        s = s.replace('```json', '').replace('```', '').strip()
    try:
        obj = json.loads(s)
        if not isinstance(obj, dict):
            return float('nan'), 'not_json_object'
        value = obj.get(attr, None)
        if value is None or value == '':
            return float('nan'), 'missing_or_blank_attribute'
        out = float(value)
    except (ValueError, TypeError, OverflowError):
        return float('nan'), 'source_parse_invalid'
    if math.isnan(out):
        return out, 'source_numeric_nan'
    if not math.isfinite(out):
        raise ValueError('Rating range/nonfinite source conflict: requires before-values disposition')
    if not 1 <= out <= 5:
        return out, 'valid_source_out_of_rubric_retained'
    return out, 'valid_source_boolean_coercion' if isinstance(value, bool) else 'valid'


def validate_map(q, all_inputs):
    if q.get('schema') != 'ROOT_QUALIFIED_COMPLETE_MENTALBENCH_ORIGINAL_MAP001':
        raise ValueError('Missing exact original-map schema')
    required = ('ROOT_exact_original_headers_and_IDs_qualified',
                'ROOT_all5_raw_workbooks_to_all4_paperdate_CSVs_qualified',
                'ROOT_complete_1000x10x7x4_original_slots_qualified',
                'ROOT_released_human_reference_aggregation_provenance_qualified',
                'ROOT_original_missingness_and_source_parser_policy_qualified')
    if any(q.get(k) is not True for k in required):
        raise ValueError('Exterior original map/provenance is unqualified')
    if q.get('all_original_input_refs') != all_inputs:
        raise ValueError('Original map must bind every exact original input')
    ids = q.get('ordered_original_identity_sha256')
    if not isinstance(ids, list) or len(ids) != 1000 or len(set(ids)) != 1000:
        raise ValueError('Exact 1000 original source identities required')
    if any(not isinstance(s, str) or len(s) != 64 or any(c not in '0123456789abcdef' for c in s) for s in ids):
        raise ValueError('Bad original identity hash')
    if set(q.get('judge_csv_maps', {})) != set(JUDGES):
        raise ValueError('All four source judge maps required')
    if q.get('three_individual_human_raters_present_claimed') is not False:
        raise ValueError('This adapter claims released reference only, not three individual raters')
    return {s: i for i, s in enumerate(ids)}


def read_all(q, all_inputs, guard):
    index = validate_map(q, all_inputs)
    values, lineage, parse_counts = {}, [], {}
    cell_hashes = bytearray()
    csv.field_size_limit(262144)
    for judge in JUDGES:
        guard()
        spec = q['judge_csv_maps'][judge]
        if spec.get('input_ref') not in all_inputs or not spec['input_ref']['path'].lower().endswith('.csv'):
            raise ValueError('Unpinned original CSV')
        headers = spec.get('exact_header')
        if not isinstance(headers, list) or len(headers) != len(set(headers)) or len(headers) > 2000:
            raise ValueError('Exact unique observed headers required')
        key = spec.get('identity_key', {})
        if key.get('kind') not in ('exact_column_utf8_sha256', 'exact_composite_utf8_fields_length_prefixed_sha256'):
            raise ValueError('No positional/default identity mapping')
        id_cols = [key.get('column')] if key['kind'] == 'exact_column_utf8_sha256' else key.get('columns')
        if not isinstance(id_cols, list) or not id_cols or len(id_cols) != len(set(id_cols)) or any(c not in headers for c in id_cols):
            raise ValueError('Original identity source column absent')
        if spec.get('encoding') not in ('utf-8', 'utf-8-sig'):
            raise ValueError('Encoding must be qualified, no fallback')
        if spec.get('delimiter') != ',' or spec.get('quotechar') != '"':
            raise ValueError('Only explicitly qualified original pandas-default CSV dialect')
        na = spec.get('exact_source_pandas_NA_lexemes')
        if not isinstance(na, list) or any(not isinstance(s, str) for s in na):
            raise ValueError('Original pandas NA lexical policy must be qualified before values')
        positions = {h: i for i, h in enumerate(headers)}
        for model in MODELS:
            for role in ('human', 'judge'):
                if f'{role}_response_{model}' not in positions:
                    raise ValueError('Missing source-fixed model/role column')
        values[judge] = {m: {a: {'human': array.array('d', [float('nan')]) * 1000,
                               'judge': array.array('d', [float('nan')]) * 1000}
                             for a in ATTRIBUTES} for m in MODELS}
        seen = set()
        with open(spec['input_ref']['path'], 'r', encoding=spec['encoding'], newline='') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"', doublequote=True, strict=True)
            if next(reader, None) != headers:
                raise ValueError('Actual original CSV header differs from qualified map')
            for ordinal, row in enumerate(reader, 1):
                if ordinal % 10 == 0:
                    guard()
                if ordinal > 1000 or len(row) != len(headers):
                    raise ValueError('Original row/width conflict; no dropping or cohort repair')
                identity_hash = hashlib.sha256()
                for col in id_cols:
                    field = row[positions[col]].encode('utf-8')
                    if key['kind'] == 'exact_composite_utf8_fields_length_prefixed_sha256':
                        identity_hash.update(len(field).to_bytes(8, 'little'))
                    identity_hash.update(field)
                identity = identity_hash.hexdigest()
                if identity not in index or identity in seen:
                    raise ValueError('Missing/duplicate/unqualified source identity')
                seen.add(identity)
                slot = index[identity]
                digest = hashlib.sha256()
                for s in row:
                    b = s.encode('utf-8')
                    digest.update(len(b).to_bytes(8, 'little'))
                    digest.update(b)
                lineage.append({'judge': judge, 'CSV_data_row_ordinal_1based': ordinal,
                                'original_identity_sha256': identity, 'canonical_slot_0based': slot,
                                'ordered_decoded_row_sha256': digest.hexdigest()})
                for model in MODELS:
                    for role in ('human', 'judge'):
                        text = row[positions[f'{role}_response_{model}']]
                        cell_hashes.extend(hashlib.sha256(text.encode('utf-8')).digest())
                        if text in na:
                            text = ''
                        for attr in ATTRIBUTES:
                            value, reason = rating(text, attr)
                            values[judge][model][attr][role][slot] = value
                            k = f'{judge}/{model}/{role}/{attr}/{reason}'
                            parse_counts[k] = parse_counts.get(k, 0) + 1
        if len(seen) != 1000:
            raise ValueError('Incomplete original cohort; full1000 required')
    return values, {'schema': 'MENTALBENCH_COMPLETE_ORIGINAL_CSV_LINEAGE001',
                    'all4000_source_rows': lineage, 'source_parse_counts': parse_counts,
                    'cell_hash_binary_order': 'judge, CSV original row, model, role human/judge;32-byte SHA256',
                    'source_cell_hash_count': len(cell_hashes) // 32,
                    'actual_three_individual_raters_read': False}, bytes(cell_hashes)
