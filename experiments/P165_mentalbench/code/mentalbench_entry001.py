"""DORMANT; requires distinct future ROOT phase authority, source/runtime/map proof.

No source approval, resource measurement, acquisition, grant, origin, or scientific
credit is produced by this entry. External native/resource ownership is NOT supplied
in this packet. BLIND_STRUCTURE is not complete schema qualification. PRIMARY needs
an accepted exterior original-map/5-workbook provenance proof which does not yet exist.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
OUTPUT_LIMIT = 32 * 1024 * 1024


def read_json(path, cap=2 * 1024 * 1024):
    with open(path, 'rb') as f:
        b = f.read(cap + 1)
    if len(b) > cap:
        raise ValueError('Metadata byte cap')
    return json.loads(b)


def instant(s):
    if not isinstance(s, str):
        raise ValueError('Explicit timezone-aware original clock string required')
    t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('Naive clock refused')
    return t.astimezone(dt.timezone.utc)


def verify_ref(r, guard, max_bytes=32 * 1024 * 1024):
    if not isinstance(r, dict) or set(('path', 'bytes', 'sha256')) - set(r):
        raise ValueError('Exact byte reference required')
    p = pathlib.Path(r['path'])
    if not p.is_absolute() or p.is_symlink() or not p.is_file() or p.stat().st_size != r['bytes'] or r['bytes'] > max_bytes:
        raise ValueError('Unqualified reference path/size')
    h, git = hashlib.sha256(), hashlib.sha1()
    git.update(('blob ' + str(r['bytes']) + '\0').encode('ascii'))
    before = p.stat()
    with open(p, 'rb') as f:
        while True:
            guard()
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            git.update(b)
    after = p.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Source/input stat raced')
    if h.hexdigest() != r['sha256'] or ('Git_blob_SHA1' in r and git.hexdigest() != r['Git_blob_SHA1']):
        raise ValueError('Source/input byte identity mismatch')
    return p


def load_local(name, ref, guard):
    p = verify_ref(ref, guard)
    if p.parent.resolve() != HERE or p.name != name + '.py':
        raise ValueError('Only exact pinned local source module allowed')
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--control', required=True)
    args = ap.parse_args()
    a = read_json(args.control)
    if a.get('execution_authorized') is not True:
        raise ValueError('Dormant control: no execution authority')
    required = ('ROOT_exact_source_review_accepted', 'ROOT_selection_and_chronology_accepted',
                'ROOT_complete_original_CENTRAL_scope_and_criteria_accepted',
                'ROOT_native_resource_and_current_peer_admission_accepted',
                'ROOT_exact_all9_original_input_bytes_acquisition_accepted')
    if any(a.get(k) is not True for k in required):
        raise ValueError('Missing separately issued ROOT authority')
    phase = a.get('phase')
    if phase not in ('BLIND_STRUCTURE', 'PRIMARY'):
        raise ValueError('Unknown exact phase')
    origin, work, end = (instant(a.get(k)) for k in ('original_origin_UTC', 'phase_work_end_UTC', 'absolute_deadline_UTC'))
    now = dt.datetime.now(dt.timezone.utc)
    if not origin <= now < work <= end or (end - origin).total_seconds() > 7200:
        raise ValueError('Unissued/expired/unadopted whole clock')
    mono_end = time.monotonic() + (work - now).total_seconds()
    def guard():
        if dt.datetime.now(dt.timezone.utc) >= work or time.monotonic() >= mono_end:
            raise RuntimeError('Original phase work cut')
    packet_path = verify_ref(a['source_packet_ref'], guard)
    packet = read_json(packet_path)
    if verify_ref(packet['entry_ref'], guard).resolve() != pathlib.Path(__file__).resolve():
        raise ValueError('Current entry byte/source identity mismatch')
    adopted = read_json(verify_ref(packet['adopted_source_method921_ref'], guard))
    if adopted.get('schema') != 'ROOT_PROSPECTIVE_P165_MENTALBENCH_SOURCE_METHOD_AND_NEAR_ADOPTION921' or adopted.get('ROOT_method_source_review_complete') is not True:
        raise ValueError('No exact adopted921 method')
    grant = read_json(verify_ref(a['ROOT_phase_grant_ref'], guard))
    if grant.get('schema') != 'ROOT_DISTINCT_MENTALBENCH_PHASE_GRANT001' or grant.get('ROOT_one_phase_explicitly_admitted') is not True:
        raise ValueError('No one-phase grant')
    for key in ('phase', 'original_origin_UTC', 'phase_work_end_UTC', 'absolute_deadline_UTC', 'source_packet_ref'):
        if grant.get(key) != a.get(key):
            raise ValueError('Grant/control exact field join')
    for key in required:
        if grant.get(key) is not True:
            raise ValueError('Grant authority leaf missing')
    for key in ('all_original_input_refs', 'programme_run_root', 'exclusive_output_directory',
                'accepted_original_map_ref', 'accepted_numpy_source_choice_ref'):
        if grant.get(key) != a.get(key):
            raise ValueError('Grant/control exact input/map/output/runtime join')
    if grant.get('ROOT_actual_tool_and_native_owner_source_ref') is None:
        raise ValueError('External native/tool owner has not been source-qualified')
    refs = a.get('all_original_input_refs')
    if not isinstance(refs, list) or len(refs) != 9 or sum(r['bytes'] for r in refs) != 30100646:
        raise ValueError('Exact nine original source files required')
    expected = packet['opaque_original_manifest']['files']
    if [(r.get('original_repo_path'), r.get('bytes'), r.get('Git_blob_SHA1')) for r in refs] != [(r['path'], r['bytes'], r['Git_blob_SHA1']) for r in expected]:
        raise ValueError('Original paper-date manifest mismatch')
    for r in refs:
        verify_ref(r, guard)
    output = pathlib.Path(a['exclusive_output_directory'])
    if not output.is_absolute() or output.exists() or output.parent.resolve() != pathlib.Path(a['programme_run_root']).resolve():
        raise ValueError('Exclusive direct-child output required')
    # Full physical programme census, links/reparse/races, memory and peer interlock
    # are external native-owner prerequisites, NOT implemented by this soft guard.
    output.mkdir(parents=False, exist_ok=False)
    written = 0
    def write(name, payload, raw=False):
        nonlocal written
        guard()
        if pathlib.PurePath(name).name != name:
            raise ValueError('Output leaf only')
        b = payload if raw else (json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')
        if written + len(b) > OUTPUT_LIMIT:
            raise ValueError('Whole current phase logical output cap')
        p = output / name
        with open(p, 'xb') as f:
            f.write(b)
            f.flush()
            os.fsync(f.fileno())
        written += len(b)
        verify = {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
        verify_ref(verify, guard)
        return verify
    if phase == 'BLIND_STRUCTURE':
        s = load_local('mentalbench_structure001', packet['module_refs']['mentalbench_structure001'], guard)
        projections = [{'input_ref': r, 'structure': s.inspect(r['path'], guard)} for r in refs]
        result = write('COMPLETE_OPAQUE_STRUCTURE_PROJECTION001.json', {
            'schema': 'MENTALBENCH_OPAQUE_STRUCTURE_PROJECTION001', 'all9': projections,
            'source_map_qualified': False, 'original_cohort_qualified': False,
            'all_scalar_values_suppressed_except_fixed_nonnumeric_source_labels': True,
            'next_status': 'HOLD_EXTERIOR_ORIGINAL_MAP_AND_RAW_TO_CSV_PROVENANCE', 'paper_credit': False})
        products = {'opaque_structure': result}
    else:
        if a.get('ROOT_exact_original_map_and_raw5_to_CSV4_join_accepted') is not True:
            raise ValueError('No complete original adapter qualification')
        q = read_json(verify_ref(a['accepted_original_map_ref'], guard))
        adapter = load_local('mentalbench_original_csv001', packet['module_refs']['mentalbench_original_csv001'], guard)
        adapter.validate_map(q, refs)
        runtime = read_json(verify_ref(a['accepted_numpy_source_choice_ref'], guard))
        if runtime.get('ROOT_exact_numpy_source_choice_accepted') is not True:
            raise ValueError('NumPy source choice unqualified')
        for r in runtime.get('all_runtime_file_refs', []):
            verify_ref(r, guard, max_bytes=64 * 1024 * 1024)
        if not runtime.get('all_runtime_file_refs'):
            raise ValueError('Exact runtime closure absent')
        for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[k] = '1'
        site = pathlib.Path(runtime['qualified_bundled_site']).resolve()
        sys.path.insert(0, str(site))  # Only the ROOT-qualified bundled namespace; no HOST site.
        import numpy as np
        if str(np.__version__) != runtime['numpy_version']:
            raise ValueError('Actual NumPy version mismatch')
        namespace = {str(pathlib.Path(r['path']).resolve()): r for r in runtime['all_runtime_file_refs']}
        used = []
        for name, mod in sorted(sys.modules.items()):
            path = getattr(mod, '__file__', None)
            if path and (name == 'numpy' or name.startswith('numpy.')):
                resolved = str(pathlib.Path(path).resolve())
                if resolved not in namespace:
                    raise ValueError('Unpinned actual NumPy module origin')
                used.append({'module': name, 'file_ref': namespace[resolved]})
        core = load_local('mentalbench_core001', packet['module_refs']['mentalbench_core001'], guard)
        target = load_local('mentalbench_targets001', packet['module_refs']['mentalbench_targets001'], guard)
        bindings = read_json(verify_ref(packet['all1150_target_binding_ref'], guard))
        values, lineage, cellhashes = adapter.read_all(q, refs, guard)
        facts = core.reduce_complete(values, np, guard)
        comparisons = target.compare_all(facts, bindings)
        directions = core.proposed_core_directions(facts)
        if any(n in sys.modules for n in ('torch', 'tensorflow', 'jax', 'pandas', 'sklearn', 'pingouin')):
            raise ValueError('Unadmitted heavy framework imported')
        used = []
        for name, mod in sorted(sys.modules.items()):
            path = getattr(mod, '__file__', None)
            if path and (name == 'numpy' or name.startswith('numpy.')):
                resolved = str(pathlib.Path(path).resolve())
                if resolved not in namespace:
                    raise ValueError('Unpinned actual late-imported NumPy module origin')
                used.append({'module': name, 'file_ref': namespace[resolved]})
        products = {'facts': write('COMPLETE_ALL28_AND_MODEL_FACTS001.json', facts),
                    'all1150_diagnostics': write('COMPLETE_ALL1150_DIAGNOSTICS001.json', comparisons),
                    'core_direction_proposals': write('PROPOSED_CORE_DIRECTIONS001.json', directions),
                    'lineage': write('COMPLETE_ALL4000_ROW_LINEAGE001.json', lineage),
                    'all80000_source_cell_hashes': write('COMPLETE_SOURCE_CELL_SHA256_BINARY001.bin', cellhashes, raw=True),
                    'actual_numpy_origin': write('ACTUAL_NUMPY_MODULE_ORIGINS001.json', {'used': used, 'runtime_ref': a['accepted_numpy_source_choice_ref']})}
    # Rehash every original input after all work. External final native/tool proof remains required.
    for r in refs:
        verify_ref(r, guard)
    write('MENTALBENCH_PHASE_CANDIDATE001.json', {'schema': 'MENTALBENCH_PHASE_CANDIDATE001',
        'phase': phase, 'candidate_complete': True, 'science_credit': False,
        'source_packet_ref': a['source_packet_ref'], 'original_origin_UTC': a['original_origin_UTC'],
        'absolute_deadline_UTC': a['absolute_deadline_UTC'], 'all_input_refs': refs,
        'products': products, 'all_output_bytes_before_candidate': written,
        'independent_audit_and_ROOT_required': True,
        'native_resource_or_final_tool_closure_claimed': False})
    guard()


if __name__ == '__main__':
    main()
