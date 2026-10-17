"""Complete original nine-checkpoint central workflow; explicit separate phase authority."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

RECOVERY_SOURCE=Path(__file__).absolute().parent
S=RECOVERY_SOURCE.parent/'source_preparation002'
sys.path.insert(0,str(S));sys.path.insert(0,str(RECOVERY_SOURCE))
import p157_gpu_phase006 as P
import p157_data002 as D
import p157_gpu_models006 as M
import p157_gpu_audit006 as A
C=P.C
MODELS=['r'+str(i)for i in range(1,9)]+['r_dyn']

def own_write_hook():
    def hook(event,args):
        if event.startswith('socket.')and event!='socket.gethostname':raise RuntimeError('Offline scientific phase forbids network')
        if event in('subprocess.Popen','os.system')or event.startswith(('os.exec','os.spawn')):raise RuntimeError('Scientific worker cannot launch other actors')
        if event=='open':
            path,mode,flags=args
            writing=isinstance(mode,str)and any(x in mode for x in 'wax+')or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing:C.require(isinstance(path,(str,bytes,os.PathLike))and Path(os.fsdecode(path)).absolute().is_relative_to(C.RUN),'Python-observed scientific write outside complete owned root')
        if event in('os.remove','os.rmdir','os.rename','os.chmod','os.utime','os.truncate','os.link','os.symlink','os.mkdir'):
            for p in args[:2]:
                if isinstance(p,(str,bytes,os.PathLike)):C.require(Path(os.fsdecode(p)).absolute().is_relative_to(C.RUN),'Python-observed filesystem mutation outside owned root')
    sys.addaudithook(hook)

def array_writer(np,out,guard):
    def write(name,value):
        p=out/(name+'.f32');p.parent.mkdir(parents=True,exist_ok=True)
        x=value.detach().cpu().contiguous().numpy();C.require(x.dtype==np.dtype('<f4'),'Whole exact FP32 array')
        v=memoryview(x).cast('B')
        with p.open('xb')as f:
            for first in range(0,len(v),1024**2):C.require(f.write(v[first:first+1024**2])==len(v[first:first+1024**2]),'Complete bounded array write')
        ref=C.pin(p);ref.update(shape=list(x.shape),dtype='<f4');guard.check('complete whole array '+name);return ref
    return write

def verify_array(ref):
    basic={k:ref[k]for k in('path','bytes','sha256')};return C.verify(basic)

def prepare(a,g,np):
    payload={x['name']:x['actual_payload_ref']['path']for x in a['_acquisition']['payloads']}
    data=D.validate_original(payload['data/multi_hop/train.json'],payload['data/multi_hop/test.json'],payload['data/multi_hop/vocab.json'],g)
    return payload,data

def full_model(t,np,model,name,data,out,g):
    own=out/name;own.mkdir();arrays=[]
    for R in range(1,41):
        lp=own/('R'+str(R).zfill(2)+'.logits.f32');ip=own/('R'+str(R).zfill(2)+'.ids.u16')
        with lp.open('xb')as f:f.truncate(29250*217*4)
        with ip.open('xb')as f:f.truncate(29250*2)
        arrays.append((np.memmap(lp,mode='r+',dtype='<f4',shape=(29250,217)),np.memmap(ip,mode='r+',dtype='<u2',shape=(29250,)),lp,ip))
    counts=np.zeros((40,39),dtype=np.int64);timing=[]
    with t.no_grad():
        for first in range(0,29250,32):
            last=min(first+32,29250);x=t.tensor(data['inputs'][first:last],dtype=t.long,device=M.DEVICE);mask=(x!=0).long();t.cuda.synchronize();start=time.monotonic()
            logits=M.prefix_logits(t,model,x,mask,g);ids=logits.argmax(-1);t.cuda.synchronize();seconds=time.monotonic()-start
            raw=logits.detach().cpu().numpy();pred=ids.detach().cpu().numpy()
            for R,(lp,ip,_,_)in enumerate(arrays):lp[first:last]=raw[R];ip[first:last]=pred[R]
            for j,k in enumerate(range(first,last)):counts[:,data['hops'][k]-2]+=(pred[:,j]==data['targets'][k]).astype(np.int64)
            timing.append({'first':first,'last':last,'seconds':seconds})
            g.check('all40 fixed depths '+name+' '+str(last))
    rec=[]
    for R,(lp,ip,lpath,ipath)in enumerate(arrays,1):
        lp.flush();ip.flush();del lp,ip
        rec.append({'R':R,'logits_ref':C.pin(lpath),'prediction_ids_ref':C.pin(ipath),'examples':29250,'vocab':217})
        g.check('whole model final array hashes '+name+' R'+str(R))
    # Drop every mapped array before the next serial model, retaining all files.
    arrays.clear()
    result={'model':name,'recurrences':rec,'correct_integer_counts_R_by_hop':counts.tolist(),'all14040_scope_contribution':1560,'every_actual_batch_timing':timing}
    C.save(own/'COMPLETE_MODEL.json',result);return result

def adaptive(t,np,model,data,out,g,eps):
    label='paper_0p01'if eps==.01 else'source_0p001';own=out/label;own.mkdir()
    paths=[own/'logits.f32',own/'ids.u16',own/'iterations.u8']
    for p,n in zip(paths,(29250*217*4,29250*2,29250)):
        with p.open('xb')as f:f.truncate(n)
    lm=np.memmap(paths[0],mode='r+',dtype='<f4',shape=(29250,217));im=np.memmap(paths[1],mode='r+',dtype='<u2',shape=(29250,));um=np.memmap(paths[2],mode='r+',dtype='u1',shape=(29250,))
    counts=[0]*39;batches=[]
    for first in range(0,29250,32):
        last=min(first+32,29250);x=t.tensor(data['inputs'][first:last],dtype=t.long,device=M.DEVICE);lengths=t.tensor(data['lengths'][first:last],dtype=t.long,device=M.DEVICE)
        result,observed=M.original_adaptive(t,model,x,lengths,eps,g)
        final=result['final_logits'][:,-1,:].detach();ids=final.argmax(-1)
        lm[first:last]=final.cpu().numpy();im[first:last]=ids.cpu().numpy();um[first:last]=result['iterations_used'].detach().cpu().numpy()
        decisions=[]
        for step in observed:decisions.append({key:(value.detach().cpu().tolist()if isinstance(value,t.Tensor)else value)for key,value in step.items()})
        for j,k in enumerate(range(first,last)):counts[data['hops'][k]-2]+=int(ids[j].item()==data['targets'][k])
        batch={'first':first,'last':last,'actual_original_decisions':decisions};batches.append(batch)
        C.append(own/'complete_actual_adaptive_decisions.jsonl',batch);g.check('original adaptive '+label+' '+str(last))
    lm.flush();im.flush();um.flush();del lm,im,um
    row={'eps_KL':eps,'entropy':3.0,'min_iters':1,'max_iters':16,'logits_ref':C.pin(paths[0]),'prediction_ids_ref':C.pin(paths[1]),'iterations_ref':C.pin(paths[2]),'correct_integer_counts_by_hop':counts,'batches':batches,'original_function_body_executed_unchanged':True,'instrumentation':'Source line observer snapshots actual pre-update KL/entropy/new_halts/halted; no predicate or value replaced.'}
    C.save(own/'COMPLETE_ADAPTIVE.json',row);return row

def main():
    p=argparse.ArgumentParser();p.add_argument('--admission',required=True);p.add_argument('--phase',choices=list(P.LIMITS),required=True);p.add_argument('--root-authorized-phase',action='store_true');args=p.parse_args()
    a=P.admission(args.admission,args.phase,args.root_authorized_phase);a['_cutoff']=a['_work_cutoff'];out=P.R.output(a,C);meta=out/('worker'if args.phase=='full'else'audit_worker006');meta.mkdir()
    g=P.Guard(a,meta);own_write_hook();g.check('before scientific import',True)
    try:
        packet=a['_packet'];static={'runtime_source_refs':packet['runtime_source_refs']}
        t,np,Config,author=M.runtime(static,g)
        runtime={'python':sys.version,'executable':C.pin(sys.executable),'torch':t.__version__,'numpy':np.__version__,'torch_origin':t.__file__,'Transformers_GPT2Block_origin':author.GPT2Block.__module__,'intra_threads':t.get_num_threads(),'interop_threads':t.get_num_interop_threads(),'CPU_only':False,'GPU_device':'cuda:0','precision':'float32','AMP':False,'TF32':False,'matmul':'highest','HIP':t.version.hip,'source_namespace':'g9 only'}
        C.save(meta/'ACTUAL_RUNTIME.json',runtime)
        payload,data=prepare(a,g,np);C.save(meta/'COMPLETE_RAW_DATA_INTEGRITY.json',data['integrity'])
        if args.phase=='full'and a['GPU_full_mode']=='GPU_SOURCE_QUALIFICATION_ONLY':
            collation=M.qualify_original_collation(t,author,data,Path(payload['data/multi_hop/test.json']).parent,g)
            C.save(meta/'COMPLETE_ORIGINAL_COLLATION_EQUIVALENCE.json',collation);models=[];adap=[]
            for name in MODELS:
                choices=[v for k,v in payload.items()if k.startswith('checkpoints/multi_hop/final_models/'+name+'/')]
                C.require(len(choices)==1,'Exactly one whole original checkpoint')
                model=M.model_from_original(t,Config,author,choices[0],g);dest=out/name;dest.mkdir()
                rows=M.fidelity(t,np,model,data,g,array_writer(np,dest,g))
                if name=='r_dyn':adap=M.qualify_adaptive(t,np,model,data,g,array_writer(np,dest,g))
                models.append({'model':name,'checkpoint_path':choices[0],'all_matched_batch_cases':rows})
                C.save(dest/'COMPLETE_GPU_SOURCE_QUALIFICATION.json',models[-1]);del model;t.cuda.synchronize();g.check('after qualification model '+name,True)
            result={'schema':'P157_COMPLETE_ALL9_ALL40_AND_BOTH_ADAPTIVE_GPU_QUALIFICATION006','admission_ref':a['_admission_ref'],
                'current_source_packet_ref':a['current_source_packet_ref'],'common_origin_UTC':a['common_origin_UTC'],
                'full_origin_UTC':a['phase_origin_UTC'],'full_work_cutoff_UTC':a['exact_absolute_full_work_cutoff_UTC'],
                'all9_all40_and_both_adaptive_qualified':True,'all29250_original_collation':collation,'models':models,'both_adaptive_matched_cases':adap,
                'bound':{'absolute':1e-4,'relative_to_source_abs':1e-4},'bitwise_is_diagnostic_only':True,
                'CPU_r1_r7_unchanged_reuse_does_not_imply_crossdevice_bitwise_equivalence':True,
                'measured_whole_remaining_forecast_and_ROOT_manual_admission_required':True,'no_automatic_remaining_full_chain':True,'paper_credit':0}
            ref=C.save(out/'COMPLETE_GPU_QUALIFICATION.json',result)
        elif args.phase=='full':
            models=P.R.retained_models(a,C);adap={}
            for name in MODELS[7:]:
                choices=[v for k,v in payload.items()if k.startswith('checkpoints/multi_hop/final_models/'+name+'/')];C.require(len(choices)==1,'All9 original checkpoint mapping')
                model=M.model_from_original(t,Config,author,choices[0],g);models.append(full_model(t,np,model,name,data,out,g))
                if name=='r_dyn':
                    for eps,label in((.01,'paper_0p01'),(.001,'source_0p001')):adap[label]=adaptive(t,np,model,data,out,g,eps)
                del model;t.cuda.synchronize();g.check('after serial remaining GPU model '+name,True)
            result={'schema':'P157_COMPLETE_ALL_NINE_FIXED_AND_BOTH_ADAPTIVE002','models':models,'adaptive':adap,'all_fixed_prediction_count':10530000,'all_fixed_accuracy_cells':14040,'all_fixed_FP32_logit_elements':10530000*217,'raw_data_integrity':data['integrity'],'common_origin_UTC':a['common_origin_UTC'],'paper_credit':0}
            result['recovery_provenance']=P.R.provenance(a);result['GPU_source_qualification_ref']=a['complete_GPU_qualification_ref'];result['mixed_device_scope']={'exact_CPU_reused':['r'+str(i)for i in range(1,8)],'new_GPU':['r8','r_dyn'],'both_adaptive_GPU':True}
            ref=C.save(out/'COMPLETE_ALL_NINE_FULL.json',result)
        else:
            full=json.loads(C.verify(a['complete_full_ref']).read_bytes());fixed=[]
            C.require([x['model']for x in full['models']]==MODELS,'Every original model in fixed order')
            for row in full['models']:fixed.append(A.audit_fixed(np,row['model'],row,data,g,verify_array))
            dynamic=full['models'][-1]
            adap=[A.audit_adaptive(np,full['adaptive'][label],data,dynamic,g,verify_array)for label in('paper_0p01','source_0p001')]
            target=json.loads(C.verify(packet['all3279_target_ref']).read_bytes());comparison=A.published_all3279(target,full)
            C.save(out/'COMPLETE_ALL3279_PUBLISHED_COMPARISON.json',comparison)
            result={'schema':'P157_COMPLETE_INDEPENDENT_WHOLE_DATA_LOGIT_COUNTER_AUDIT002','fixed':fixed,'adaptive':adap,'complete_full_ref':a['complete_full_ref'],'all3279_published_AND':comparison['all_published_cells_AND'],'scientific_central_conjunction':comparison['all_published_cells_AND'],'operational_audit_complete':True,'independent_full_neural_forward_rerun':False,'credit_requires_ROOT_final_native_time_resource_and_whole_outcome_review':True,'paper_credit':0}
            ref=C.save(out/'COMPLETE_WHOLE_AUDIT.json',result)
        # Complete original input custody is checked again after the phase, including weights.
        for row in a['_acquisition']['payloads']:C.verify(row['actual_payload_ref'])
        P.R.verify_preserved(a,C)
        C.save(meta/'COMPLETE_IMPORTED_G9_MODULE_CUSTODY.json',M.imported_module_custody(g))
        g.check('after full phase receipt/input hashes',True)
        print(json.dumps({'phase':args.phase,'operational_complete':True,'result_ref':ref,'paper_credit':0}),flush=True)
        g.observation('final actual postwrite/hash/stdout',True);return 0 if C.utc()<a['_cutoff']else 1
    except BaseException as e:
        failure={'UTC':C.iso(),'phase':args.phase,'admission_ref':a['_admission_ref'],'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'every_partial_preserved_no_automatic_retry':True,'paper_credit':0}
        try:C.save(meta/'FAILURE.json',failure)
        except Exception as secondary:failure['secondary_failure_receipt_error']=repr(secondary)
        print(json.dumps(failure),flush=True);return 1
if __name__=='__main__':raise SystemExit(main())
