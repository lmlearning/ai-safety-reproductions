"""Separate current phase admission, original common origin and direct owned child."""
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

S=Path(__file__).absolute().parent
OLD=S.parent/'source_preparation001/p157_common001.py'
spec=importlib.util.spec_from_file_location('p157_frozen_acquisition_common001',OLD);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
LIMITS={'fidelity':21600,'full':475200,'audit':10800}

def resource_append(path,row):
    raw=(json.dumps(row,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    C.require(len(raw)<=4096,'Full unthinned resource row exceeds fixed4096B format cap: '+json.dumps(row))
    with Path(path).open('ab')as f:C.require(f.write(raw)==len(raw),'Complete resource row write')

def admission(path,phase,explicit):
    C.require(explicit and phase in LIMITS,'Explicit ROOT current scientific-phase command required')
    a=json.loads(Path(path).read_bytes())
    C.require(a.get('execution_authorized')is True and a.get('root_P157_same_programme_phase_admitted')is True and a['phase']==phase,'No current P157 scientific phase admission')
    grant=json.loads(C.verify(a['common_grant_ref']).read_bytes())
    C.require(grant['schema']=='P157_ONE_144H_PROGRAMME_GRANT001'and grant['execution_authorized']is True and grant['phase_authorized']=='acquisition','Original immutable first grant provenance')
    C.require(grant['total_seconds']==518400 and grant['stage_cumulative_cutoffs_seconds']==C.CUTOFFS,'No original clock extension')
    start=dt.datetime.fromisoformat(grant['common_origin_UTC']);end=dt.datetime.fromisoformat(grant['common_deadline_UTC'])
    C.require(start.tzinfo is not None and end-start==dt.timedelta(seconds=518400),'One fixed common clock')
    phase_start=dt.datetime.fromisoformat(a['phase_origin_UTC'])
    C.require(a['common_origin_UTC']==grant['common_origin_UTC']and phase_start>=start,'Same origin, separately observed phase admission')
    cutoff=min(start+dt.timedelta(seconds=C.CUTOFFS[phase]),phase_start+dt.timedelta(seconds=LIMITS[phase]))
    C.require(C.utc()>=phase_start and C.utc()<cutoff,'Current absolute common/local phase window')
    review=json.loads(C.verify(a['source_review_ref']).read_bytes())
    C.require(review.get('root_complete_P157_scientific_source_review_passed')is True and review['current_source_packet_ref']==a['current_source_packet_ref'],'Current whole scientific source review')
    packet=json.loads(C.verify(a['current_source_packet_ref']).read_bytes())
    for r in packet['current_source_refs']:C.verify(r)
    C.require(a['preregistration_ref']==C.pin(C.PREREG),'Fixed whole scope/preregistration')
    for key in ('P092_CPU_audit_terminal_ref','ROOT_complete_acquisition_acceptance_ref','complete_acquisition_ref'):C.verify(a[key])
    acq=json.loads(Path(a['complete_acquisition_ref']['path']).read_bytes())
    C.require(acq['operational_complete']is True and len(acq['payloads'])==12,'All12 original payloads')
    for row in acq['payloads']:C.verify(row['actual_payload_ref'])
    if phase in('full','audit'):
        fid=json.loads(C.verify(a['complete_fidelity_ref']).read_bytes())
        C.require(fid['all9_models_all40_matched_batch_full_logits_bitwise_equal']is True and len(fid['models'])==9,'Whole reviewed source-prefix fidelity first')
        C.require(a.get('ROOT_measured_timing_and_memory_full_stage_admission_ref')is not None,'Measured throughput must justify full stage beyond old24h plan')
        C.verify(a['ROOT_measured_timing_and_memory_full_stage_admission_ref'])
    if phase=='audit':C.verify(a['complete_full_ref'])
    a.update(_phase=phase,_start=start,_cutoff=cutoff,_work_cutoff=cutoff-dt.timedelta(seconds=60),_admission_ref=C.pin(path),_common_grant=grant,_acquisition=acq,_packet=packet)
    return a

class Guard:
    def __init__(self,a,out,parent=False):
        self.a=a;self.out=Path(out);self.native=C.Native();self.last_native=-1e30;self.last_census=-1e30;self.last=None;self.parent=parent
        self.roots=[(C.INPUT,C.INPUT_CAP),(C.RUN,C.SCIENCE_CAP)]
    def observation(self,label,census=False,terminal=None):
        storage=C.census(self.native,self.roots)if census else None
        n=self.native.read();working=max(n['working'],n['peak_working']);private=max(n['private'],n['peak_pagefile'])
        if terminal is not None:working+=terminal['peak_working'];private+=max(terminal['private'],terminal['peak_pagefile'])
        C.require(working<=int(4.5*C.GiB)and private<=int(6.5*C.GiB),'Whole direct pair4.5/6.5GiB lifetime upper-bound peaks')
        if self.parent:C.require(max(n['working'],n['peak_working'])<=64*1024**2,'Parent64MiB working peak')
        C.require(n['available_RAM']>=C.GiB and n['available_commit']>=8*C.GiB,'Continuous1GiB RAM/8GiB commit')
        C.require(C.utc()<self.a['_cutoff'],'Original same-common/local absolute cutoff after all observations')
        return {'UTC':C.iso(),'label':label,'phase':self.a['_phase'],'native':n,'complete_owned_storage':storage,'shared_elapsed_seconds':(C.utc()-self.a['_start']).total_seconds()}
    def check(self,label,force=False):
        if not force and time.monotonic()-self.last_native<5:
            C.require(C.utc()<self.a['_cutoff'],'Absolute phase cutoff');return self.last
        full=force or time.monotonic()-self.last_census>=30
        row=self.observation(label,full)
        if full:self.last_census=time.monotonic()
        resource_append(self.out/'resources.jsonl',row);self.last_native=time.monotonic();self.last=row;return row

def parent(args):
    a=admission(args.admission,args.phase,args.root_authorized_phase)
    C.safe_root(C.RUN);out=C.RUN/args.phase
    C.require(not out.exists(),'Preserve every old phase/partial; no automatic restart')
    out.mkdir(parents=True);meta=out/'parent';meta.mkdir();cache=C.RUN/'temp_cache';cache.mkdir(exist_ok=True)
    g=Guard(a,meta,True);fresh=g.observation('fresh phase admission',True)
    C.require(fresh['native']['available_RAM']>=5*C.GiB and fresh['native']['available_commit']>=12*C.GiB,'Fresh5GiB RAM/12GiB commit before scientific import')
    env=os.environ.copy();env.update(TMP=str(cache),TEMP=str(cache),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='12',MKL_NUM_THREADS='12',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(cache/'hf'),TORCH_HOME=str(cache/'torch'))
    command=[sys.executable,'-I','-S','-B','-X','utf8',str(S/'p157_science002.py'),'--admission',str(Path(args.admission).absolute()),'--phase',args.phase,'--root-authorized-phase']
    child=None;initial=terminal=None;failure=None;errors=[];closed=False
    try:
        C.save(meta/'COMMAND.json',{'argv':command,'admission_ref':a['_admission_ref'],'fresh':fresh,'environment_overrides':{k:env[k]for k in('TMP','TEMP','OMP_NUM_THREADS','MKL_NUM_THREADS','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HOME','TORCH_HOME')},'scope':'One current retained child; no all-descendant/Job/DLL or parent-postexit claim'})
        with (meta/'child.stdout').open('xb')as stdout,(meta/'child.stderr').open('xb')as stderr:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,creationflags=0x08000000)
            initial=g.native.read(int(child._handle));C.require(initial['pid']==child.pid,'Actual retained direct child')
            while child.poll()is None:
                C.require(C.utc()<a['_work_cutoff'],'Same phase60s closure reserve reached')
                g.check('parent live');n=g.native.read(int(child._handle),initial)
                row=g.observation('live complete pair',False,n);row['child']=n;resource_append(meta/'direct_child_samples.jsonl',row);time.sleep(1)
            terminal=g.native.read(int(child._handle),initial);g.observation('terminal whole pair',True,terminal)
            C.require(child.returncode==0 and terminal['native_exit_or_STILL_ACTIVE']==0,'Whole scientific phase child failed')
    except BaseException as e:failure={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    finally:
        if child is not None:
            try:
                if child.poll()is None:child.terminate();child.wait(timeout=5)
                terminal=g.native.read(int(child._handle),initial)
            except Exception as e:errors.append({'exact_owned_cleanup':repr(e)})
            try:child._handle.Close();closed=True
            except Exception as e:errors.append({'owned_direct_handle_close':repr(e)})
        result={'UTC':C.iso(),'admission_ref':a['_admission_ref'],'initial_child':initial,'terminal_child':terminal,'Popen_returncode':None if child is None else child.returncode,'failure':failure,'cleanup_errors':errors,'owned_direct_handle_closed':closed,'parent_postexit_native':'UNMEASURED','failure_cleanup_may_use_at_most5s_beyond_cutoff_no_acceptance':True,'paper_credit':0}
        C.save(meta/'TERMINAL.json',result)
    complete=failure is None and not errors and closed
    print(json.dumps({'phase':args.phase,'operational_complete':complete,'terminal_ref':C.pin(meta/'TERMINAL.json'),'paper_credit':0}),flush=True)
    try:g.observation('final actual postreceipt/hash/stdout/census',True,terminal)
    except Exception as e:print(json.dumps({'final_acceptance_failure':repr(e)}),flush=True);return 1
    return 0 if complete and C.utc()<a['_cutoff']else 1

def main():
    p=argparse.ArgumentParser();p.add_argument('--admission',required=True);p.add_argument('--phase',choices=list(LIMITS),required=True);p.add_argument('--root-authorized-phase',action='store_true');return parent(p.parse_args())
if __name__=='__main__':raise SystemExit(main())
