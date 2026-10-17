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

def require(ok,message):
    if not ok:raise RuntimeError(message)

def runtime(static_proposal,guard):
    """Called only after separate ROOT phase admission, never during acquisition."""
    for row in static_proposal['packages']:
        p=Path(row['METADATA_ref']['path']);require(hashlib.sha256(p.read_bytes()).hexdigest()==row['METADATA_ref']['sha256'],'Runtime package metadata pin')
    std=[str(Path(sys.base_prefix)/'Lib'),str(Path(sys.base_prefix)/'DLLs'),str(Path(sys.base_prefix)/'python312.zip')]
    sys.path[:]=[str(CPU),str(TRANSFORMERS)]+std
    guard.check('before CPU scientific imports',force=True)
    import torch
    import numpy as np
    import transformers
    from transformers import GPT2Config
    from transformers.models.gpt2.modeling_gpt2 import GPT2Block
    require(torch.__version__=='2.7.1+cpu' and torch.version.hip is None and torch.version.cuda is None,'Pinned CPU-only torch')
    require(transformers.__version__=='4.52.4','Pinned compatible GPT2 source stack')
    require(Path(torch.__file__).is_relative_to(CPU) and Path(np.__file__).is_relative_to(CPU),'CPU import origins')
    require(Path(transformers.__file__).is_relative_to(TRANSFORMERS),'Transformers import origin')
    torch.set_num_threads(12);torch.set_num_interop_threads(1)
    torch.set_float32_matmul_precision('highest')
    require(torch.get_num_threads()==12 and torch.get_num_interop_threads()==1,'Exact CPU thread allocation')
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    spec=importlib.util.spec_from_file_location('p157_original_author_model',AUTHOR);author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    guard.check('after CPU scientific imports',force=True)
    return torch,np,GPT2Config,author

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
    model.load_state_dict(sd,strict=True);model.to(t.device('cpu'));model.eval()
    require(sum(p.numel()for p in model.parameters())==28519680,'Whole original four-layer28,519,680-parameter model')
    require(not model.input_injection and model.positional_embedding_type=='none'and all(not m.training for m in model.modules()),'Original NoPE/no injection/dropout off')
    require(all(p.dtype==t.float32 and p.device.type=='cpu'for p in model.parameters()),'No quantization/precision/backend replacement')
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

def fidelity(t,np,model,data,guard,write_array):
    """All39 hop-first cases plus actual firstB32 and actual finalB2, all originalR."""
    first=[data['hops'].index(h)for h in range(2,41)]
    cases=[('first_39_hops_B32',first[:32]),('remaining_7_hops_B7',first[32:]),('actual_first_full_batch_B32',list(range(32))),('actual_final_batch_B2',[29248,29249])]
    rows=[]
    with t.no_grad():
        for label,indices in cases:
            x=t.tensor([data['inputs'][i]for i in indices],dtype=t.long);mask=(x!=0).long()
            start=time.monotonic();optimized=prefix_logits(t,model,x,mask,guard);prefix_seconds=time.monotonic()-start
            own=write_array(label+'_prefix',optimized)
            original=[];seconds=[]
            for recurrence in range(1,41):
                guard.check('before original fidelity '+label+' R'+str(recurrence))
                model.num_iterations=recurrence;start=time.monotonic();v=model(input_ids=x,attention_mask=mask).logits[:,-1,:].clone()
                seconds.append(time.monotonic()-start);original.append(v)
                require(t.isfinite(v).all()and t.equal(v,optimized[recurrence-1]),'Bitwise complete-vocab source-prefix mismatch: '+label+' R'+str(recurrence))
                require(t.equal(v.argmax(-1),optimized[recurrence-1].argmax(-1)),'Bitwise complete prediction-ID mismatch')
            original=t.stack(original);ref=write_array(label+'_original',original)
            require(original.dtype==optimized.dtype==t.float32,'Fidelity exact FP32')
            rows.append({'label':label,'source_indices':[data['source_indices'][i]for i in indices],'heldout_indices':indices,'batch_size':len(indices),'all40_recurrences':True,'full_vocab_size':217,'original_logits_ref':ref,'prefix_logits_ref':own,'all_full_logits_and_IDs_bitwise_equal':True,'prefix_seconds':prefix_seconds,'original_R_seconds':seconds})
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
