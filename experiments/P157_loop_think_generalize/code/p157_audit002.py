"""Independent all-example/logit/counter and exact published interval audit; inert."""
from collections import Counter
import hashlib
import json
from pathlib import Path

def require(ok,message):
    if not ok:raise RuntimeError(message)

def interval_accept(correct,total,intervals):
    require(type(correct)is int and type(total)is int and 0<=correct<=total and total==750,'Complete exact correct/750 integers')
    for b in intervals:
        d=b['denominator'];lo=b['lower_numerator'];hi=b['upper_numerator']
        require(type(d)is int and d==256 and type(lo)is int and type(hi)is int and hi==lo+1 and b['lower_inclusive']is True,'Frozen complete LUT bin geometry')
        lower=correct*d>=lo*total
        upper=correct*d<=hi*total if b['upper_inclusive']else correct*d<hi*total
        if lower and upper:return True
    return False

def audit_fixed(np,model,row,prepared,guard,verify_ref):
    """Freshly stream every retained FP32 value and independently derive each ID/count."""
    hops=np.asarray(prepared['hops'],dtype=np.int64);targets=np.asarray(prepared['targets'],dtype=np.int64)
    require(Counter(hops.tolist())==Counter({x:750 for x in range(2,41)}),'Every audit hop full denominator')
    nums=np.zeros((40,39),dtype=np.int64);sample_count=0;all_elements=0
    require(len(row['recurrences'])==40 and [r['R']for r in row['recurrences']]==list(range(1,41)),'All40 retained source recurrences')
    for rec in row['recurrences']:
        path=verify_ref(rec['logits_ref']);ids_path=verify_ref(rec['prediction_ids_ref'])
        require(rec['logits_ref']['bytes']==29250*217*4 and rec['prediction_ids_ref']['bytes']==29250*2,'All complete full-vocabulary/ID bytes')
        logits=np.memmap(path,mode='r',dtype='<f4',shape=(29250,217));ids=np.memmap(ids_path,mode='r',dtype='<u2',shape=(29250,))
        for first in range(0,29250,256):
            last=min(first+256,29250);x=np.asarray(logits[first:last]);pred=x.argmax(axis=-1)
            require(np.isfinite(x).all(),'Every retained full-vocabulary logit finite')
            require(np.array_equal(pred,ids[first:last]),'Independent every-example first-max argmax/retained ID')
            for j in range(first,last):nums[rec['R']-1,hops[j]-2]+=int(pred[j-first]==targets[j])
            sample_count+=last-first;all_elements+=(last-first)*217
            guard.check('independent full logits '+model+' R'+str(rec['R'])+' '+str(first))
        del logits,ids
    require(nums.tolist()==row['correct_integer_counts_R_by_hop'],'Every independently rebuilt integer count')
    require(sample_count==40*29250 and all_elements==40*29250*217,'Whole model audit coverage')
    return {'model':model,'all40x29250_prediction_IDs_verified':sample_count,'all_FP32_logit_elements_verified':all_elements,'complete_correct_counts':nums.tolist(),'all_full_logits_finite':True}

def audit_adaptive(np,row,prepared,fixed_row,guard,verify_ref):
    eps=row['eps_KL'];require(eps in(.01,.001),'Both fixed adaptive variants')
    logits=np.memmap(verify_ref(row['logits_ref']),mode='r',dtype='<f4',shape=(29250,217))
    ids=np.memmap(verify_ref(row['prediction_ids_ref']),mode='r',dtype='<u2',shape=(29250,))
    iterations=np.memmap(verify_ref(row['iterations_ref']),mode='r',dtype='u1',shape=(29250,))
    require(np.isfinite(logits).all()and np.array_equal(logits.argmax(-1),ids),'Every actual original adaptive logit/ID')
    fixed={r['R']:np.memmap(verify_ref(r['logits_ref']),mode='r',dtype='<f4',shape=(29250,217))for r in fixed_row['recurrences']if r['R']<=16}
    cursor=0;counts=[0]*39
    for batch in row['batches']:
        first,last=batch['first'],batch['last'];require(first==cursor and last==min(first+32,29250),'Complete exact original source batch order')
        n=last-first;chosen=[16]*n;halted=[False]*n;expected_step=2
        for step in batch['actual_original_decisions']:
            require(step['recurrence']==expected_step,'No lost source adaptive step');expected_step+=1
            for key in ('kl','entropy','new_halts','halted_before'):require(len(step[key])==n,'Full source decision geometry')
            for j in range(n):
                require(type(step['new_halts'][j])is bool and type(step['halted_before'][j])is bool,'Exact actual source booleans')
                require(step['halted_before'][j]==halted[j],'Actual source complete halt state')
                actual=(not halted[j])and step['kl'][j]<eps and step['entropy'][j]<3.0
                require(actual==step['new_halts'][j],'Every actual source KL/entropy predicate checked without recomputing neural forwards')
                if actual:halted[j]=True;chosen[j]=step['recurrence']
        require(2<=expected_step<=17 and (all(halted)or expected_step==17),'Original full16 or all-halted stop')
        require(chosen==iterations[first:last].tolist(),'Every original selected recurrence/iteration')
        for j in range(n):
            k=first+j;require(np.array_equal(logits[k],fixed[chosen[j]][k]),'All-vocabulary source adaptive choice equals matching qualified fixed prefix')
            counts[prepared['hops'][k]-2]+=int(int(ids[k])==prepared['targets'][k])
        cursor=last;guard.check('independent whole adaptive eps='+str(eps)+' '+str(last))
    require(cursor==29250 and counts==row['correct_integer_counts_by_hop'],'Complete adaptive counts and source decisions')
    del logits,ids,iterations,fixed
    return {'eps_KL':eps,'examples_verified':29250,'all_actual_decision_predicates_and_selected_full_logits_verified':True,'correct_integer_counts':counts,'no_independent_neural_forward_rerun_claim':True}

def published_all3279(target_doc,full_manifest):
    models={x['model']:x for x in full_manifest['models']};primary=full_manifest['adaptive']['paper_0p01'];rows=[]
    require(set(models)=={'r'+str(i)for i in range(1,9)}|{'r_dyn'},'All nine complete original models')
    for panel in target_doc['panels']:
        for cell in panel['cells']:
            model=cell['model'];hop=cell['hop'];R=cell['inference_recurrence']
            numerator=primary['correct_integer_counts_by_hop'][hop-2]if R=='adaptive'else models[model]['correct_integer_counts_R_by_hop'][R-1][hop-2]
            passed=interval_accept(numerator,750,cell['all_possible_accuracy_intervals'])
            rows.append({'model':model,'hop':hop,'inference_recurrence':R,'correct':numerator,'total':750,'every_source_RGB_inverse_bin':cell['all_possible_accuracy_intervals'],'passed':passed})
    require(len(rows)==3279 and len({(x['model'],x['hop'],str(x['inference_recurrence']))for x in rows})==3279,'Whole published3279-cell family, no duplicate/subset')
    return {'all3279_records':rows,'published_cell_count':3279,'all_published_cells_AND':all(x['passed']for x in rows),'passed_cells':sum(x['passed']for x in rows),'conditional_digitization_only_no_unreleased_raw_accuracy_claim':True,'no_scientific_tolerance_added':True}
