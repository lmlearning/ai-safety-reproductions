"""Original author model execution and source-proven prefix reuse; inert functions."""
import ast
from collections import OrderedDict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

ROOT=Path('{{REPRODUCTION_ROOT}}')
AUTHOR=ROOT/'literature/loop_think_generalize_source_oct15_001/source__gpt_utils_extrapolation.py'
CPU=ROOT/'environment/p092_cpu_stage_001/venv/Lib/site-packages'
TRANSFORMERS=ROOT/'environment/p026_cpu_source_amended_001/venv/Lib/site-packages'
G9=ROOT/'g9/Lib/site-packages'
DEVICE='cuda:0'
ABS_BOUND=1e-4
REL_BOUND=1e-4

def require(ok,message):
    if not ok:raise RuntimeError(message)

def runtime(static_proposal,guard):
    """Only the already qualified HOST/g9 namespace; no CPU-site shadowing or installs."""
    for r in static_proposal['runtime_source_refs']:guard.C.verify(r)
    std=[str(Path(sys.base_prefix)/'Lib'),str(Path(sys.base_prefix)/'DLLs'),str(Path(sys.base_prefix)/'python312.zip')]
    sys.path[:]=[str(G9)]+std
    guard.check('before existing g9 scientific imports',force=True)
    import torch
    import numpy as np
    import transformers
    from transformers import GPT2Config
    from transformers.models.gpt2.modeling_gpt2 import GPT2Block
    require(torch.__version__=='2.13.0+rocm10.0.0' and torch.version.hip and torch.version.cuda is None,'Existing exact HOST ROCm torch')
    require(transformers.__version__=='4.57.1' and np.__version__=='2.3.4','Existing g9 Transformers/NumPy')
    require(all(Path(m.__file__).absolute().is_relative_to(G9)for m in(torch,np,transformers)),'g9 module origins only')
    require(torch.cuda.is_available()and torch.cuda.device_count()==1,'Exactly one existing qualified GPU')
    torch.set_num_threads(12);torch.set_num_interop_threads(1)
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    require(torch.get_num_threads()==12 and torch.get_num_interop_threads()==1,'Original CPU thread allocation')
    require(torch.get_float32_matmul_precision()=='highest' and not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32,'FP32 highest/noTF32')
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
    require(not torch.is_autocast_enabled(),'No AMP/autocast')
    spec=importlib.util.spec_from_file_location('p157_original_author_model',AUTHOR);author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    guard.gpu=torch;guard.check('after existing g9 scientific imports',force=True)
    return torch,np,GPT2Config,author

def imported_module_custody(guard):
    rows=[]
    for name,module in sorted(sys.modules.items()):
        p=getattr(module,'__file__',None)
        if not isinstance(p,str):continue
        p=Path(p).absolute()
        if p.is_relative_to(G9):rows.append(dict(name=name,ref=guard.C.pin(p)))
        elif 'site-packages'in p.parts:require(False,'Scientific dependency outside exact g9: '+name)
    return rows

def model_from_original(t,GPT2Config,author,path,guard):
    guard.check('before original checkpoint interpretation',force=True)
    config=GPT2Config(vocab_size=217,n_positions=50,n_ctx=50,n_embd=768,n_layer=4,n_head=12,_attn_implementation='eager')
    model=author.RecurrentGPT2Block(config,1,positional_embedding_type='none',input_injection=False)
    # Safe tensor/state interpreter only; never fall back to arbitrary pickle execution.
    checkpoint=t.load(path,map_location=t.device('cpu'),weights_only=True)
    require(type(checkpoint)is dict and 'model_state_dict'in checkpoint,'Original checkpoint model_state_dict')
    sd=checkpoint['model_state_dict'];require(type(sd)in(dict,OrderedDict),'Complete original state dictionary')
    prefix=[k.startswith('_orig_mod.')for k in sd]
    require(all(prefix)or not any(prefix),'Reject mixed/ambiguous original compile prefix')
    if any(prefix):sd={k[len('_orig_mod.'):]:v for k,v in sd.items()}
    require(all(isinstance(v,t.Tensor)and v.dtype==t.float32 and v.device.type=='cpu'and t.isfinite(v).all()for v in sd.values()),'All complete original FP32 finite CPU weights')
    require(t.equal(sd['lm_head.weight'],sd['token_embedding.weight']),'Original exact tied embedding/head weights')
    model.load_state_dict(sd,strict=True);model.to(device=t.device(DEVICE),dtype=t.float32);model.eval()
    require(sum(p.numel()for p in model.parameters())==28519680,'Whole original four-layer28,519,680-parameter model')
    require(not model.input_injection and model.positional_embedding_type=='none'and all(not m.training for m in model.modules()),'Original NoPE/no injection/dropout off')
    require(all(p.dtype==t.float32 and p.device.type=='cuda'for p in model.parameters()),'No quantization/precision/backend replacement')
    del checkpoint,sd
    guard.check('after complete original model load',force=True)
    return model

def qualify_original_collation(t,author,data,data_dir,guard):
    vocab,size=author.load_vocab(str(Path(data_dir)/'vocab.json'))
    require(vocab==data['vocab']and size==217,'Original load_vocab every literal token and index')
    dataset=author.CompositionTestDataset(str(data_dir),'test.json',vocab,all_splits=[f'{h}hop_test'for h in range(2,41)])
    require(len(dataset)==29250,'Original complete all_splits selection')
    batches=0
    for first in range(0,29250,32):
        last=min(first+32,29250)
        original=author.custom_collate_test([dataset[i]for i in range(first,last)],max_len=50)
        x,y,mask,lengths,types=original
        own=t.tensor(data['inputs'][first:last],dtype=t.long)
        require(t.equal(x,own)and t.equal(mask,(own!=0).long()),'All original token IDs and masks source-order bitwise')
        require(t.equal(y,t.tensor(data['targets'][first:last],dtype=t.long)),'All original target IDs bitwise')
        require(t.equal(lengths,t.tensor(data['lengths'][first:last],dtype=t.long)),'All original source input lengths')
        require(list(types)==[str(h)+'hop_test'for h in data['hops'][first:last]],'All original held-out types/order')
        batches+=1;guard.check('all original collation/source ordering '+str(last))
    del dataset
    return {'all_original_examples':29250,'all_original_batches':batches,'batch_size':32,'final_batch_size':2,'all_original_input_target_mask_length_and_type_values_bitwise_equal':True}

def prefix_logits(t,model,input_ids,attention_mask,guard):
    """Identical source NoPE embeddings, masks and ordered blocks; heads do not mutate h."""
    require(model.positional_embedding_type=='none'and not model.input_injection and not model.training,'Reviewed source-only branch')
    h=model.dropout(model.token_embedding(input_ids))
    mask=attention_mask.unsqueeze(1).unsqueeze(2).to(dtype=h.dtype)
    mask=(1.0-mask)*-10000.0
    values=[]
    for recurrence in range(1,41):
        for block in model.blocks:h=block(h,attention_mask=mask)[0]
        # Keep full source head shape; selecting h[:,-1] before matmul can change kernels.
        logits=model.lm_head(model.ln_f(h))
        values.append(logits[:,-1,:].clone())
        require(t.isfinite(values[-1]).all(),'All final-position FP32 logits finite')
        guard.check('original prefix recurrence '+str(recurrence))
    return t.stack(values,dim=0)

def compare_logits(np,source_value,candidate_value,label):
    """All elements; fixed FP32 bound. Every argmax flip and propagated margin retained."""
    source=np.asarray(source_value,dtype=np.float32);candidate=np.asarray(candidate_value,dtype=np.float32)
    require(source.shape==candidate.shape and source.ndim>=2 and source.shape[-1]==217,'Complete matched vocabulary geometry')
    require(np.isfinite(source).all()and np.isfinite(candidate).all(),'Every matched element finite')
    s=source.astype(np.float64);c=candidate.astype(np.float64);error=np.abs(c-s);bound=ABS_BOUND+REL_BOUND*np.abs(s)
    flat=s.reshape(-1,217);other=c.reshape(-1,217);errors=error.reshape(-1,217);bounds=bound.reshape(-1,217)
    flips=[];robust_violations=[]
    for i in range(len(flat)):
        sid=int(flat[i].argmax());cid=int(other[i].argmax())
        competitors=flat[i].copy();competitors[sid]=-np.inf;second=int(competitors.argmax())
        margin=float(flat[i,sid]-flat[i,second]);propagated=float(bounds[i,sid]+bounds[i,second])
        # Every competitor is included; the highest source competitor need not have the largest error bound.
        all_margin_safe=all(float(flat[i,sid]-flat[i,j])>float(bounds[i,sid]+bounds[i,j])for j in range(217)if j!=sid)
        if sid!=cid:
            row=dict(flat_vector_index=i,source_argmax=sid,candidate_argmax=cid,source_top_two_margin=margin,top_two_propagated_bound=propagated,
                flipped_competitor_margin=float(flat[i,sid]-flat[i,cid]),flipped_pair_propagated_bound=float(bounds[i,sid]+bounds[i,cid]),
                actual_flipped_pair_error=float(errors[i,sid]+errors[i,cid]),all_competitors_margin_certified=bool(all_margin_safe),near_tie=not bool(all_margin_safe))
            flips.append(row)
            if all_margin_safe:robust_violations.append(row)
    return dict(label=label,shape=list(source.shape),elements=int(source.size),absolute_bound=ABS_BOUND,relative_bound=REL_BOUND,
        maximum_absolute_error=float(error.max()),maximum_fraction_of_bound=float((error/bound).max()),all_elements_within_bound=bool((error<=bound).all()),
        bitwise_equal_diagnostic_only=bool(np.array_equal(source,candidate)),argmax_differences=flips,all_argmax_differences_reported=True,
        margin_certified_argmax_violations=robust_violations,near_ties_do_not_automatically_veto=True,
        qualified=bool((error<=bound).all())and not robust_violations)

def fidelity(t,np,model,data,guard,write_array):
    """Same four original cases/all40, plus both unchanged source adaptive paths for rdyn externally."""
    rows=[]
    with t.no_grad():
        for label,indices in matched_cases(data):
            x=t.tensor([data['inputs'][i]for i in indices],dtype=t.long,device=DEVICE);mask=(x!=0).long()
            t.cuda.synchronize();start=time.monotonic();optimized=prefix_logits(t,model,x,mask,guard);t.cuda.synchronize();prefix_seconds=time.monotonic()-start
            own=write_array(label+'_prefix',optimized);original=[];seconds=[]
            for recurrence in range(1,41):
                guard.check('before original GPU fidelity '+label+' R'+str(recurrence))
                model.num_iterations=recurrence;t.cuda.synchronize();start=time.monotonic()
                v=model(input_ids=x,attention_mask=mask).logits[:,-1,:].clone();t.cuda.synchronize()
                seconds.append(time.monotonic()-start);original.append(v)
            original=t.stack(original);ref=write_array(label+'_original',original)
            require(original.dtype==optimized.dtype==t.float32,'Qualification exact FP32')
            comparison=compare_logits(np,original.detach().cpu().numpy(),optimized.detach().cpu().numpy(),label)
            row={'label':label,'source_indices':[data['source_indices'][i]for i in indices],'heldout_indices':indices,'batch_size':len(indices),
                'all40_recurrences':True,'full_vocab_size':217,'original_logits_ref':ref,'prefix_logits_ref':own,'comparison':comparison,
                'prefix_seconds':prefix_seconds,'original_R_seconds':seconds}
            rows.append(row);guard.C.save(Path(own['path']).parent/(label+'_COMPLETE_COMPARISON.json'),row)
            require(comparison['qualified'],'Whole matched GPU source/prefix comparison failed; all arrays and comparison retained')
    model.num_iterations=1
    return rows

def matched_cases(data):
    first=[data['hops'].index(h)for h in range(2,41)]
    return [('first_39_hops_B32',first[:32]),('remaining_7_hops_B7',first[32:]),('actual_first_full_batch_B32',list(range(32))),('actual_final_batch_B2',[29248,29249])]

def qualify_adaptive(t,np,model,data,guard,write_array):
    rows=[]
    for label,indices in matched_cases(data):
        x=t.tensor([data['inputs'][i]for i in indices],dtype=t.long,device=DEVICE)
        lengths=t.tensor([data['lengths'][i]for i in indices],dtype=t.long,device=DEVICE)
        with t.no_grad():prefix=prefix_logits(t,model,x,(x!=0).long(),guard)
        for eps in(.01,.001):
            result,observed=original_adaptive(t,model,x,lengths,eps,guard)
            actual=result['final_logits'][:,-1,:].detach();used=result['iterations_used'].detach()
            require(bool(((used>=1)&(used<=16)).all()),'All source adaptive selected depths')
            selected=t.stack([prefix[int(used[j].item())-1,j]for j in range(len(indices))])
            tag=label+'_eps_'+str(eps);actual_ref=write_array(tag+'_adaptive',actual);selected_ref=write_array(tag+'_selected_prefix',selected)
            comparison=compare_logits(np,actual.cpu().numpy(),selected.cpu().numpy(),tag)
            row=dict(label=label,eps_KL=eps,heldout_indices=indices,iterations_used=used.cpu().tolist(),actual_adaptive_logits_ref=actual_ref,
                selected_prefix_logits_ref=selected_ref,comparison=comparison,
                actual_original_decisions=[{key:(value.detach().cpu().tolist()if isinstance(value,t.Tensor)else value)for key,value in step.items()}for step in observed])
            rows.append(row);guard.C.save(Path(actual_ref['path']).parent/(tag+'_COMPLETE_ADAPTIVE_COMPARISON.json'),row)
            require(comparison['qualified'],'Matched unchanged adaptive/prefix GPU bound failed')
    model.num_iterations=1
    return rows

def original_adaptive(t,model,x,lengths,eps,guard):
    """Run unchanged author adaptive function; observe all actual decisions before mutation."""
    require(eps in(.01,.001),'Exactly paper-primary/released-wrapper secondary thresholds')
    require(sys.gettrace()is None,'No conflicting Python instrumentation')
    raw=AUTHOR.read_text(encoding='utf8');tree=ast.parse(raw)
    method=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='forward_adapative')
    watch=next(n.lineno for n in ast.walk(method)if isinstance(n,ast.If)and ast.unparse(n.test)=='new_halts.any()')
    observations=[];code=model.forward_adapative.__func__.__code__
    def observe(frame,event,arg):
        if frame.f_code is not code:return None
        if event=='line'and frame.f_lineno==watch:
            v=frame.f_locals
            observations.append({'recurrence':int(v['t'])+1,'kl':v['kl'].detach().clone(),'entropy':v['entropy'].detach().clone(),'new_halts':v['new_halts'].detach().clone(),'halted_before':v['halted'].detach().clone()})
            require(len(observations)<=15,'All bounded source adaptive decisions')
        return observe
    model.num_iterations=16;guard.check('before unchanged original adaptive eps='+str(eps))
    sys.settrace(observe)
    try:
        with t.no_grad():result=model.forward_adapative(input_ids=x,attention_mask=(x!=0).long(),input_lengths=lengths,pred_pos='last_token',eps_kl=eps,entropy_thresh=3.0,min_iters=1)
    finally:sys.settrace(None)
    require(result['final_logits'].dtype==t.float32 and t.isfinite(result['final_logits']).all(),'All original adaptive logits finite')
    guard.check('after unchanged original adaptive eps='+str(eps))
    return result,observations
