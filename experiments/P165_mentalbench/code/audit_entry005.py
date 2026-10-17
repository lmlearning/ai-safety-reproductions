"""Dormant full independent original-input audit entry. No import-time science."""
import argparse,datetime as dt,hashlib,importlib,json,os,sys
from pathlib import Path
W=Path('{{REPRODUCTION_ROOT}}')
POLICY_SHA='91ae5fe0a367fb50d9d805b62effc338b5def17959f48010c1d55b8afd901850'
def need(x,m):
    if not x:raise ValueError(m)
def pin(p):
    p=Path(p).resolve();h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def load(q,cap=33554432):
    need(type(q)is dict and set(q)=={'path','bytes','sha256'},'exactref');need(0<q['bytes']<=cap,'metadata read cap');need(pin(q['path'])==q,'metadata source pin');return json.loads(Path(q['path']).read_bytes())
def save(p,x):
    b=(json.dumps(x,separators=(',',':'),allow_nan=False)+'\n').encode();need(len(b)<=67108864,'ROOT prospective64MiB single JSON cap')
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--control',required=True);args=ap.parse_args();cp=Path(args.control).resolve();need(cp.stat().st_size<=65536,'control cap');c=json.loads(cp.read_bytes())
    for k in ('execution_authorized','ROOT_independent_source_reviewed','ROOT_original_map_and_all9_provenance_accepted','ROOT_source_target_binding_and_API_bridge_accepted','ROOT_runtime_and_native_owner_admitted','ROOT_primary_closed_products_accepted','ROOT_original_paperdate_CSV_missingness_is_analysis_input_accepted'):need(c[k] is True,k)
    origin=dt.datetime.fromisoformat(c['original_origin_UTC']);end=dt.datetime.fromisoformat(c['absolute_deadline_UTC']);work=dt.datetime.fromisoformat(c['phase_work_end_UTC']);need(origin.tzinfo and end.tzinfo and work.tzinfo and (end-origin).total_seconds()==7200 and origin<dt.datetime.now(dt.timezone.utc)<work<=end,'original7200clock')
    def clock():need(dt.datetime.now(dt.timezone.utc)<work,'audit work deadline')
    packet=load(c['source_packet_ref']);need(packet['entry_ref']==pin(__file__),'current audit entry')
    for q in packet['all_code_refs']:need(pin(q['path'])==q,'independent code pin')
    policy=load(c['adopted921_ref']);need(c['adopted921_ref']['sha256']==POLICY_SHA and policy['ROOT_candidate_source_eligible'] is True,'exact921')
    mapping=load(c['accepted_original_map_ref']);runtime=load(c['accepted_runtime_ref']);exterior=load(c['accepted_exterior_provenance_ref']);target_acceptance=load(c['accepted_target_binding_ref'])
    need(exterior['ROOT_complete_all5_workbooks_to4_CSVs_accepted'] is True and exterior['all_original_input_refs']==mapping['all_original_input_refs'],'exterior5workbook provenance')
    need(target_acceptance['ROOT_fixed_before_values_source_semantic_bindings_accepted'] is True and target_acceptance['binding_ref']==c['source_target_bindings_ref'] and target_acceptance['catalogue_ref']==c['source_catalogue_ref'],'before-values target DATA acceptance')
    raw952=load(c['raw952_semantic_diagnostic_ref']);need(raw952['all80000_cells']==80000 and raw952['all560000_attributes']==560000,'complete952 diagnostic; no exact-equality veto')
    need(runtime.get('ROOT_exact_numpy_source_choice_accepted') is True,'adopted929 exact NumPy source choice; actual version/origin checked below')
    for q in runtime['all_runtime_file_refs']:need(pin(q['path'])==q,'runtimefile pin')
    out=Path(c['exclusive_output_directory']).resolve();need(out.is_relative_to(W) and not out.exists(),'exclusive audit namespace');out.mkdir()
    code=Path(__file__).resolve().parent;corepath=Path(packet['core_ref']['path']).resolve();sys.path.insert(0,str(code));sys.path.insert(0,str(corepath.parent));sys.path.insert(0,runtime['qualified_bundled_site'])
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):need(os.environ.get(key)=='1','fixed singlethread environment '+key)
    np=importlib.import_module('numpy');need(np.__version__==runtime['numpy_version'] and Path(np.__file__).resolve().is_relative_to(Path(runtime['qualified_bundled_site']).resolve()),'actual qualified NumPy origin')
    from original_reader005 import read_originals
    from independent_mentalbench_core001 import reduce_all,bootstrap_design,fixed_contrast_operands
    from semantic_bridge005 import project,compare_primary,source_targets
    clock();hashpath=out/'ALL80000_ORIGINAL_CSV_CELL_SHA256.bin';reasonpath=out/'ALL560000_ATTRIBUTE_REASON_CODES.bin'
    human,pairs,ids,lineage=read_originals(mapping,hashpath,reasonpath);lineage['raw952_semantic_diagnostic_ref']=c['raw952_semantic_diagnostic_ref'];lineage['raw952_counts']=raw952['counts'];clock()
    design=bootstrap_design(np);facts=reduce_all(human,pairs,ids,design);clock();canonical=project(facts)
    targets=source_targets(canonical,load(c['source_catalogue_ref']),load(c['source_target_bindings_ref']));contrasts=fixed_contrast_operands(facts)
    # Own original-input facts are complete BEFORE opening primary result JSON.
    primary=load(c['closed_primary_facts_ref']);comparison=compare_primary(canonical,primary);clock()
    products={}
    for role,name,value in [('independent_full_facts','INDEPENDENT_ALL28_AND_MODEL_FACTS005.json',canonical),('all1150_source_diagnostics','INDEPENDENT_ALL1150_DIAGNOSTICS005.json',targets),('all_comparison_roles','COMPLETE_PRIMARY_INDEPENDENT_COMPARISON005.json',comparison),('central_contrast_operands','INDEPENDENT_CENTRAL_CONTRASTS005.json',contrasts),('original_lineage','INDEPENDENT_COMPLETE_ORIGINAL_LINEAGE005.json',lineage),('raw_draw_provenance','INDEPENDENT_ALL28000_RAW_DRAW_RECORDS005.json',{j:{a:v['bootstrap']['independent_draw_records'] if v['bootstrap'] else None for a,v in attrs.items()} for j,attrs in facts['all28_cells'].items()})]:products[role]=save(out/name,value)
    products['original_CSV_cell_hashes']=pin(hashpath);products['original_attribute_reason_codes']=pin(reasonpath)
    need(hashpath.stat().st_size==80000*32 and reasonpath.stat().st_size==80000*7,'complete source-cell custody cardinality')
    for q in mapping['all_original_input_refs']:need(pin(q['path'])=={k:q[k]for k in ('path','bytes','sha256')},'postwrite original pin')
    need(sum(q['bytes'] for q in products.values())<=134217728,'audit logical partition within whole256MiB')
    for q in packet['all_code_refs']:need(pin(q['path'])==q,'postwrite source pin')
    clock();candidate=dict(schema='MENTALBENCH_PHASE_CANDIDATE001',phase='INDEPENDENT_AUDIT',candidate_complete=True,science_credit=False,source_packet_ref=c['source_packet_ref'],original_origin_UTC=c['original_origin_UTC'],absolute_deadline_UTC=c['absolute_deadline_UTC'],all_input_refs=mapping['all_original_input_refs'],products=products,all_output_bytes_before_candidate=sum(q['bytes'] for q in products.values()),independent_audit_and_ROOT_required=True,native_resource_or_final_tool_closure_claimed=False,original_all9_read_independently=True,full1000_record_slots=True,all1150_source_operands_reported=True,diagnostic_agreement=all(x['status']=='TRUE' for x in comparison),near_award_pending_ROOT=True,primary_reducer_imported=False)
    q=save(out/'MENTALBENCH_PHASE_CANDIDATE001.json',candidate);print(json.dumps({'candidate_ref':q,'science_credit':False}),flush=True)
if __name__=='__main__':main()
