"""Same original clocks; exact seven-model reuse and complete remaining fixed/adaptive/audit workflow."""
import datetime as dt
import json
from pathlib import Path

def verify_preserved(a,C):
 old=json.loads(C.verify(a['closed_failed_full_custody_ref']).read_bytes());C.require(old['whole_closed_custody']['complete']is True,'Original failedfull custody')
 C.require(old['immutable_authority']['admission_ref']==a['original_failed_full_admission_ref'],'Exact original failedfull authority')
 root=C.RUN/'full';refs=old['whole_closed_custody']['file_refs'];C.require({str(p.absolute())for p in root.rglob('*')if p.is_file()}=={r['path']for r in refs},'Original failedfull no additions/drops')
 for r in refs:C.require(Path(r['path']).is_relative_to(root),'Original custody root');C.verify({k:r[k]for k in('path','bytes','sha256')});C.require(C.utc()<a['_work_cutoff'],'Same workcut during original custody')
 qual=json.loads(C.verify(a['_packet']['retained_metadata_ref']).read_bytes());inv=qual['closed004_inventory'];root=C.RUN/'recovery_full004'
 C.require(Path(inv['root'])==root and inv['file_count']==575,'Fixed closed004 metadata root')
 C.require({str(p.absolute())for p in root.rglob('*')if p.is_file()}=={r['path']for r in inv['files']},'Entire closed004 namespace preserved')
 current=[]
 for r in inv['files']:
  p=Path(r['path']);C.safe_root(p);C.require(p.stat().st_size==r['bytes'],'Closed004 metadata size unchanged');current.append(C.pin(p));C.require(C.utc()<a['_work_cutoff'],'Same workcut during closed004 opaque hashing')
 if '_closed004_refs'in a:C.require(current==a['_closed004_refs'],'No closed004 bytes changed during newphase')
 else:a['_closed004_refs']=current
 # Every reused complete model and array has an original, already saved hash; verify all560 arrays without interpreting values.
 for row in qual['models']:
  model=json.loads(C.verify(row['manifest_ref']).read_bytes());C.require(model['model']==row['model'],'Retained model identity')
  C.require([r['R']for r in model['recurrences']]==list(range(1,41))and len(model['every_actual_batch_timing'])==915,'Complete retained40/915')
  C.require([(x['first'],x['last'])for x in model['every_actual_batch_timing']]==[(i,min(i+32,29250))for i in range(0,29250,32)],'All retained batch extents exact')
  C.require(model['recurrences']==row['metadata_projection']['recurrences'],'Retained original40recurrence refs unchanged')
  for rec in model['recurrences']:
   C.require(rec['examples']==29250 and rec['vocab']==217,'Whole original geometry')
   for key,size in [('logits_ref',29250*217*4),('prediction_ids_ref',29250*2)]:C.require(rec[key]['bytes']==size,'Whole complete array size');C.verify(rec[key]);C.require(C.utc()<a['_work_cutoff'],'Retained array opaque hash workcut')
 return old

def validate_admission(a,C):
 C.require(a['_phase']in('full','audit')and a.get('same_programme_recovery_authorized')is True,'Explicit current sameprogramme phase')
 packet=a['_packet'];review=json.loads(C.verify(a['source_review_ref']).read_bytes())
 C.require(review.get('root_complete_P157_same_programme_recovery_source_review_passed')is True and review['current_recovery_False_control_refs']==packet['False_control_refs'],'Whole006 GPU review/control joins')
 false=json.loads(C.verify(packet['False_control_refs'][control_key(a)]).read_bytes());expected=dict(false)
 for k in('execution_authorized','root_P157_same_programme_phase_admitted','same_programme_recovery_authorized'):expected[k]=True
 for k in('source_review_ref','current_source_packet_ref','current_joint_resource_review_ref','ROOT_existing_g9_runtime_acceptance_ref'):expected[k]=a[k]
 if a['_phase']=='full'and a['GPU_full_mode']=='GPU_REMAINING_FULL':
  for k in('ROOT_closed_GPU_qualification_acceptance_ref','complete_GPU_qualification_ref','ROOT_GPU_measured_remaining_full_admission_ref'):expected[k]=a[k]
 if a['_phase']=='audit':
  for k in('phase_origin_UTC','complete_full_ref','ROOT_current_full_native_acceptance_ref'):expected[k]=a[k]
 C.require({k:v for k,v in a.items()if not k.startswith('_')}==expected,'Only fixed authority/currentaudit links may change')
 old=json.loads(C.verify(a['original_failed_full_admission_ref']).read_bytes());C.require(a['common_grant_ref']==old['common_grant_ref']and a['common_origin_UTC']==old['common_origin_UTC'],'Original common grant/origin')
 C.require(a['common_origin_UTC']=='2026-10-15T13:28:33.952532+00:00'and a['original_total_programme_seconds']==518400,'Original144h common clock')
 for key in('work_reserve_before_phase_end_seconds','common_full_cumulative_cutoff_seconds','original_total_programme_seconds','exact_absolute_full_inclusive_cutoff_UTC','exact_absolute_full_work_cutoff_UTC','external_growth_reserves_bytes','external_current_growth_reserves_bytes'):C.require(a[key]==old[key],'No original clock/reservation change '+key)
 if a['_phase']=='full':C.require(a['phase_origin_UTC']==old['phase_origin_UTC']=='2026-10-15T15:22:10.276826+00:00'and a['local_inclusive_max_seconds']==475200,'Same132h full origin')
 else:
  C.require(a['local_inclusive_max_seconds']==10800,'Original3h mandatoryaudit')
  accepted=json.loads(C.verify(a['ROOT_current_full_native_acceptance_ref']).read_bytes());C.require(accepted.get('ROOT_complete_P157_current_full_native_and_products_accepted')is True and accepted['complete_full_ref']==a['complete_full_ref']and accepted['current_source_packet_ref']==a['current_source_packet_ref'],'Fullclosed qualification before separate audit')
 joint=json.loads(C.verify(a['current_joint_resource_review_ref']).read_bytes());C.require(joint.get('ROOT_P157_recovery_joint_resources_passed')is True and joint.get('P157_input4GiB_and_science14GiB_reserves_active')is True and joint.get('ROOT_prior_P157_release_revoked_or_not_applied')is True,'Current full reservations remain')
 C.require(joint['current_recovery_source_packet_ref']==a['current_source_packet_ref']and joint.get('ROOT_P019_heavy_phase_closed_before_serial_P157')is True and joint.get('no_other_heavy_phase_at_admission')is True,'SerialP019closed prerequisite')
 for k in('foreign_unspent_bytes','maximum_operative_RAM_floor_bytes','maximum_operative_commit_floor_bytes','maximum_operative_fresh_RAM_bytes','maximum_operative_fresh_commit_bytes'):C.require(type(joint[k])is int and joint[k]>=0,'Finite maximum operative peer floors')
 a['_joint']=joint
 C.require(joint.get('ROOT_current_P019_GPU_native_tool_closed_and_BOTH_sync_apps_restored')is True,'Current GPU owner closed/BOTHrestored; old926/962 is not currentGPU proof')
 C.verify(joint['current_P019_GPU_closed_and_BOTH_restore_ref'])
 runtime=json.loads(C.verify(a['ROOT_existing_g9_runtime_acceptance_ref']).read_bytes())
 C.require(runtime.get('ROOT_existing_HOST_g9_ROCm_runtime_source_and_prior_kernel_qualification_accepted')is True and runtime['current_source_packet_ref']==a['current_source_packet_ref'],'Existing g9 source/runtime qualification')
 C.require(runtime['runtime_source_refs']==packet['runtime_source_refs'],'Exact pinned g9 namespace sources')
 if a['_phase']=='full'and a['GPU_full_mode']=='GPU_REMAINING_FULL':
  accepted=json.loads(C.verify(a['ROOT_closed_GPU_qualification_acceptance_ref']).read_bytes());qualification=json.loads(C.verify(a['complete_GPU_qualification_ref']).read_bytes())
  C.require(accepted.get('ROOT_complete_all9_all40_and_both_adaptive_GPU_source_qualification_native_tool_closed')is True and accepted['current_source_packet_ref']==a['current_source_packet_ref']and accepted['complete_GPU_qualification_ref']==a['complete_GPU_qualification_ref'],'Closed qualified whole GPU prefix test before remaining full')
  C.require(qualification['all9_all40_and_both_adaptive_qualified']is True and qualification['common_origin_UTC']==a['common_origin_UTC']and qualification['current_source_packet_ref']==a['current_source_packet_ref'],'Exact qualification data/source/clock')
  forecast=json.loads(C.verify(a['ROOT_GPU_measured_remaining_full_admission_ref']).read_bytes())
  C.require(forecast.get('ROOT_GPU_remaining_whole_full_time_memory_storage_review_accepted')is True and forecast['current_source_packet_ref']==a['current_source_packet_ref']and forecast['complete_GPU_qualification_ref']==a['complete_GPU_qualification_ref'],'Actual measured whole-work forecast, not CPU or GPU-memory addition')
  C.require(forecast['full_work_cutoff_UTC']==a['exact_absolute_full_work_cutoff_UTC'],'No forecast clock reset')
 closed=json.loads(C.verify(a['closed004_and_BOTH_apps926_ref']).read_bytes());C.require(closed['strict_current_writer_and_parent_closed']is True and closed['BOTH_approved_sync_apps_restored_and_observed']is True,'Closed004/BOTHrestore proof')
 stopped=json.loads(C.verify(packet['stopped004_terminal_ref']).read_bytes());C.require(stopped['admission_ref']==a['stopped004_admission_ref']and stopped['owned_direct_handle_closed']is True and stopped['terminal_child']['native_exit_or_STILL_ACTIVE']==1,'Exact failed004 stopped authority/closure')
 C.require(closed['source_terminal_ref']==packet['stopped004_terminal_ref'],'Exact ROOT926/current004 terminal join')
 C.require(a['retained_model_manifest_refs']==packet['retained_model_manifest_refs'],'Fixed allseven reuse before outcomes');verify_preserved(a,C);return a

def retained_models(a,C):
 # Exact original JSON manifests including all counts pass unchanged to independent audit; no outcome-based selection.
 return [json.loads(C.verify(r).read_bytes())for r in a['retained_model_manifest_refs']]

def provenance(a):
 return dict(recovery_transport='SAME_ORIGINAL_CLOCK_GPU_CONTINUATION006',retained_model_manifest_refs=a['retained_model_manifest_refs'],closed004_and_BOTH_apps926_ref=a['closed004_and_BOTH_apps926_ref'],original_failed_full_admission_ref=a['original_failed_full_admission_ref'],closed_failed_full_custody_ref=a['closed_failed_full_custody_ref'],original_common_origin_UTC=a['common_origin_UTC'],original_full_origin_UTC='2026-10-15T15:22:10.276826+00:00',new_clock_or_budget=False,retained_models=['r'+str(i)for i in range(1,8)],old_partial_r8_preserved_and_NOT_reused=True,new_entire_models=['r8','r_dyn'],both_original_adaptive_eps=[.01,.001],independent_whole_audit_all3279_required=True,paper_credit=0)

def control_key(a):
 if a['_phase']=='audit':return 'audit'
 mode=a.get('GPU_full_mode');CANDIDATES={'GPU_SOURCE_QUALIFICATION_ONLY':'full_qualification','GPU_REMAINING_FULL':'full_remaining'}
 if mode not in CANDIDATES:raise RuntimeError('Explicit fixed GPU mode; no automatic qualification/full chain')
 return CANDIDATES[mode]

def output(a,C):return C.RUN/'recovery_gpu006'/('qualification'if control_key(a)=='full_qualification'else'full')
