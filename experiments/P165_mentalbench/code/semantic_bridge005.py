"""Field transport and fixed source-data target comparison, not primary arithmetic."""
import math
from decimal import Decimal
def need(x,m):
    if not x:raise ValueError(m)
def get(root,path):
    for key in path:root=root[key]
    return root
def project(core):
    cells={};paired={j:{} for j in core['all28_cells']};hm={};jm={j:{} for j in core['all28_cells']}
    cellkeys=('icc_c1','icc_a1','msr','msc','anova_mse','n_models','included_models','excluded_model','equal_weight_human_mean','equal_weight_llm_mean','equal_weight_bias','normalized_abs_equal_weight_bias','bootstrap','c1_ci_width','width_status','paired_masks_hex_little_endian')
    ba={'bias':'bland_altman_mean_difference','difference_sample_sd':'bland_altman_difference_sd_ddof1','loa_lower':'bland_altman_lower_LoA','loa_upper':'bland_altman_upper_LoA','bias_se':'bland_altman_bias_SE','loa_se':'bland_altman_LoA_SE'}
    for j,attrs in core['all28_cells'].items():
        cells[j]={}
        for a,c in attrs.items():
            x={k:c[k] for k in cellkeys};pe=c['paired_error'];x['paired_error']={k:v for k,v in pe.items() if k not in ('BlandAltman','reason')}
            for k,v in ba.items():x['paired_error'][v]=None if pe['BlandAltman'] is None else pe['BlandAltman'][k]
            if x['bootstrap'] is not None:x['bootstrap']={k:v for k,v in x['bootstrap'].items() if k!='independent_draw_records'}
            cells[j][a]=x
            for m,v in c['all10_model_pair_means'].items():paired[j].setdefault(m,{})[a]=dict(human=v['human'],judge=v['llm'],paired_valid_n=v['n_pairs'],full_original_n=1000)
        for m,attrs in core['judge_model_facts'][j].items():jm[j][m]={a:v['unpaired_llm_mean'] for a,v in attrs.items() if isinstance(v,dict)}
    for m,attrs in core['human_reference_model_facts'].items():hm[m]={a:dict(mean=v['mean'],valid_n=v['n_valid'],full_original_n=1000) for a,v in attrs.items() if isinstance(v,dict)}
    display_models=('claude','ds_llama','ds_qwen','gemini','gpt4o','gpt4omini','llama_3','qwen_2','qwen_3')
    humanavg={m:core['human_reference_model_facts'][m]['average7'] for m in display_models};judgeavg={j:{m:mm[m]['average7'] for m in display_models} for j,mm in core['judge_model_facts'].items()}
    def ranks(v):
        good=[x for x in v.values() if x is not None];return {k:None if x is None else 1+sum(y>x for y in good) for k,x in v.items()}
    allavg={m:None if any(judgeavg[j][m] is None for j in judgeavg) else math.fsum(judgeavg[j][m] for j in judgeavg)/len(judgeavg) for m in humanavg}
    return dict(all28_cells=cells,all_model_paired_means=paired,human_all_valid_model_means=hm,judge_all_valid_model_means=jm,shared_bootstrap_seed_index_design=core['shared_bootstrap_seed_index_design'],display_derivatives=dict(human_model_average=humanavg,judge_model_average=judgeavg,judge_model_rank={j:ranks(v) for j,v in judgeavg.items()},all_judge_average=allavg,all_judge_rank=ranks(allavg)))
def compare_primary(actual,primary):
    rows=[]
    def rec(a,b,path):
        if isinstance(a,dict):
            if not isinstance(b,dict):rows.append(dict(path=path,status='FALSE',reason='mapping missing'));return
            for k,v in a.items():
                if k not in b:rows.append(dict(path=path+[k],status='FALSE',reason='required field absent'))
                else:rec(v,b[k],path+[k])
        elif isinstance(a,list):
            if not isinstance(b,list) or len(a)!=len(b):rows.append(dict(path=path,status='FALSE',reason='full list coverage'));return
            for i,(x,y) in enumerate(zip(a,b)):rec(x,y,path+[i])
        elif a is None or b is None:rows.append(dict(path=path,status='TRUE' if a is b else 'FALSE',independent=a,primary=b,reason='verified semantic both-undefined' if a is b else 'definedness mismatch'))
        elif type(a) in (int,float) and type(b) in (int,float):
            error=abs(a-b);bound=1e-8*(1+max(abs(a),abs(b)));discrete=type(a)is int
            rows.append(dict(path=path,status='TRUE' if (a==b if discrete else math.isfinite(b) and error<=bound) else 'FALSE',independent=a,primary=b,error=error,diagnostic_tolerance=0 if discrete else bound))
        else:rows.append(dict(path=path,status='TRUE' if a==b and type(a)is type(b) else 'FALSE',independent=a,primary=b))
    rec(actual,primary,[]);return rows
def source_targets(facts,catalogue,binding):
    # The external True control binds this exact source-only DATA catalogue.
    # Shared source semantics do not imply shared primary estimator code.
    targets=[]
    for cell in catalogue['targets']:
        for i,(lex,dp) in enumerate(zip(cell['numeric_lexemes'],cell['display_decimal_places']),1):
            targets.append(dict(id=cell['id']+'/numeric'+str(i),source_lexeme=cell['source_lexeme'],lex=lex,dp=dp,published_table=cell['published_table']))
    rows=binding['bindings'];need(len(targets)==len(rows)==1150,'1122 source cells, all1150 numeric operands')
    need([t['id'] for t in targets]==[t['target_id'] for t in rows],'exact source catalogue order/IDs')
    result=[]
    for t,b in zip(targets,rows):
        need(b['published_numeric_lexeme']==t['lex'] and b['display_decimal_places']==t['dp'],'literal source changed')
        path=b['metric_path'];required=t['published_table'] in (2,3,4);bound=b['proposed_primary_NEAR_abs_bound']
        if required:
            need(path is not None and bound is not None,'all324main targets mapped/bounded before values')
            table=t['published_table'];leaf=path[-1]
            expected_bound=.05 if table==2 else (.10 if leaf=='mse' else .05) if table==4 else .03 if leaf in ('icc_c1','icc_a1') else .07 if leaf=='c1_ci_width' else .05
            need(bound==expected_bound,'fixed921 natural-scale bound, no changed tolerance from bindingDATA')
        value=None if path is None else get(facts,path);expected=Decimal(t['lex'].replace('\u2212','-'))
        if value is None:result.append(dict(source_id=t['id'],metric_path=path,actual=None,expected=t['lex'],literal='UNKNOWN',near='UNKNOWN' if required else 'DIAGNOSTIC',source_method_note=b['source_method_note']));continue
        need(type(value) in (int,float) and math.isfinite(value),'finite target operand');actual=Decimal(value) if type(value)is int else Decimal.from_float(value);error=abs(actual-expected);half=Decimal(5).scaleb(-t['dp']-1)
        literal=actual==expected if t['dp']==0 else error<=half
        near=None if not required else error<=Decimal(str(bound))
        result.append(dict(source_id=t['id'],metric_path=path,actual=value,expected=t['lex'],absolute_error=str(error),printed_half_unit=str(half),literal='TRUE' if literal else 'FALSE',near='DIAGNOSTIC' if not required else 'TRUE' if near else 'FALSE',source_method_note=b['source_method_note']))
    return result
