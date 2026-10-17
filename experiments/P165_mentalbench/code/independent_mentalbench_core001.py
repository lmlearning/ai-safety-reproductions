"""Dormant independent arithmetic. Never imports or invokes primary/source reducers.

No module-level experiment or numerical call. Future original-reader inputs and
runtime must be separately qualified; this file confers no execution authority.
"""
import math

MODELS=('claude','ds_llama','ds_qwen','gemini','gpt4o','gpt4omini','llama_3','qwen_2','qwen_3','human')
JUDGES=('Claude','GPT-4o','Gemini','o4-mini')
ATTRS=('Guidance','Informativeness','Relevance','Safety','Empathy','Helpfulness','Understanding')
EXCLUDED=dict(zip(JUDGES,('claude','gpt4o','gemini','gpt4omini')))

def require(ok,message):
    if not ok: raise ValueError(message)

def finite(x):
    return type(x) in (int,float) and math.isfinite(x)

def mean(x):
    return math.fsum(x)/len(x) if x else None

def sd(x,ddof=1):
    if len(x)<=ddof: return None
    m=mean(x)
    return math.sqrt(math.fsum((z-m)**2 for z in x)/(len(x)-ddof))

def ratio(x,y):
    return x/y if y!=0 else None

def interval_width(lo,hi):
    return hi-lo if lo is not None and hi is not None else None

def mask_hex(bits):
    # Equivalent to NumPy packbits(bitorder='little'); no NumPy needed.
    out=bytearray((len(bits)+7)//8)
    for i,b in enumerate(bits):
        if b: out[i//8]|=1<<(i%8)
    return out.hex()

def anova_icc(h,l):
    """Independent residual-form ANOVA, avoiding total-minus-effects cancellation."""
    require(len(h)==len(l),'paired model means')
    n=len(h)
    if n<2 or not all(finite(x) for x in h+l):
        return dict(icc_c1=None,icc_a1=None,msr=None,msc=None,anova_mse=None,reason='insufficient/nonfinite model means')
    hm,lm=mean(h),mean(l); grand=(hm+lm)/2
    row=[(x+y)/2 for x,y in zip(h,l)]
    ssr=2*math.fsum((z-grand)**2 for z in row)
    ssc=n*((hm-grand)**2+(lm-grand)**2)
    sse=math.fsum((x-z-hm+grand)**2+(y-z-lm+grand)**2 for x,y,z in zip(h,l,row))
    msr=ssr/(n-1);msc=ssc;mse=sse/(n-1)
    return dict(icc_c1=ratio(msr-mse,msr+mse),icc_a1=ratio(msr-mse,msr+mse+2*(msc-mse)/n),msr=msr,msc=msc,anova_mse=mse,reason=None)

def linear_quantile(values,q):
    require(0<=q<=1,'quantile probability')
    if not values:return None
    z=sorted(values);position=(len(z)-1)*q;lo=math.floor(position);hi=math.ceil(position)
    return z[lo]+(position-lo)*(z[hi]-z[lo])

def bootstrap_design(qualified_legacy_numpy):
    """ONLY future qualified NumPy RandomState, not default_rng or global RNG state."""
    seeds=[int(x) for x in qualified_legacy_numpy.random.RandomState(42).randint(0,100000,size=1000)]
    draws=[[int(i) for i in qualified_legacy_numpy.random.RandomState(s).choice(9,size=9,replace=True)] for s in seeds]
    return dict(all1000_integer_seeds=seeds,all1000_model_index_draws=draws,model_index_base=0)

def bootstrap(h,l,design):
    require(len(h)==len(l)==9,'full nine included models')
    require(len(design['all1000_integer_seeds'])==len(design['all1000_model_index_draws'])==1000,'complete bootstrap design')
    rawc=[];rawa=[];joint=[];cm=[];am=[];records=[]
    for seed,ix in zip(design['all1000_integer_seeds'],design['all1000_model_index_draws']):
        require(type(seed)is int and 0<=seed<100000 and len(ix)==9 and all(type(i)is int and 0<=i<9 for i in ix),'legacy seed/index record')
        v=anova_icc([h[i] for i in ix],[l[i] for i in ix]);c,a=v['icc_c1'],v['icc_a1']
        bad=c is None or a is None or not finite(c) or not finite(a)
        # Source bootstrap wrapper returns BOTH NaN if either ICC is NaN.
        rc,ra=(None,None) if bad else (c,a)
        kc=rc is not None and 0<=rc<=1;ka=ra is not None and 0<=ra<=1
        rawc.append(rc);rawa.append(ra);joint.append(bad);cm.append(kc);am.append(ka)
        records.append(dict(seed=seed,model_indices=ix,pre_wrapper_c1=c,pre_wrapper_a1=a,joint_undefined=bad,c1_kept=kc,a1_kept=ka,reason='joint undefined' if bad else ('author filter rejected one or both' if not(kc and ka) else None)))
    def summary(raw,keep):
        v=[x for x,k in zip(raw,keep) if k];alpha=1-.95
        return dict(valid=len(v),discarded=1000-len(v),lower=linear_quantile(v,alpha/2) if len(v)>=10 else None,upper=linear_quantile(v,1-alpha/2) if len(v)>=10 else None,mean=mean(v),std_ddof0=sd(v,0))
    c=summary(rawc,cm);a=summary(rawa,am)
    return dict(c1=c,a1=a,source_n_valid_samples=min(c['valid'],a['valid']),all_1000_raw_c1=rawc,all_1000_raw_a1=rawa,joint_nan_mask_hex_little_endian=mask_hex(joint),c1_author_filter_mask_hex_little_endian=mask_hex(cm),a1_author_filter_mask_hex_little_endian=mask_hex(am),independent_draw_records=records)

def paired_error(h,l):
    require(len(h)==len(l),'paired raw lengths');n=len(h)
    if n<2:
        return dict(n_pairs=n,human_mean=None,llm_mean=None,bias=None,mse=None,rmse=None,human_std=None,llm_std=None,pearson_r=None,lins_ccc=None,scale_shift=None,BlandAltman=None,reason='source requires at least two raw pairs')
    hm,lm=mean(h),mean(l);d=[y-x for x,y in zip(h,l)];bias=mean(d);mse=mean([x*x for x in d]);hs,ls=sd(h),sd(l)
    cov=math.fsum((x-hm)*(y-lm) for x,y in zip(h,l))/(n-1)
    pearson=cov/(hs*ls) if hs and ls else None
    ccc=2*cov/(hs*hs+ls*ls+(hm-lm)**2) if pearson is not None else None
    ds=sd(d);bse=ds/math.sqrt(n);lse=ds*math.sqrt(3/n)
    ba=dict(bias=bias,difference_sample_sd=ds,loa_lower=bias-1.96*ds,loa_upper=bias+1.96*ds,bias_se=bse,loa_se=lse,bias_ci_lower=bias-1.96*bse,bias_ci_upper=bias+1.96*bse,n_points=n)
    return dict(n_pairs=n,human_mean=hm,llm_mean=lm,bias=bias,mse=mse,rmse=math.sqrt(mse),human_std=hs,llm_std=ls,pearson_r=pearson,lins_ccc=ccc,scale_shift=ls/hs if hs and ls else None,BlandAltman=ba,reason=None)

def _value(v):
    require(v is None or finite(v),'finite parsed scalar or explicitly reasoned missing value')
    return v

def reduce_all(human_grid,pair_grid,context_ids,design):
    """Canonical slots must come from a future independent ORIGINAL nine-bank reader.

    human_grid[model][attribute]: 1000 values in accepted context order.
    pair_grid[judge][attribute][model]: 1000 (human,judge) tuples, same IDs.
    None represents a retained parse/missing observation, never an omitted row.
    Original cell/lexeme/reason/source linkage lives in the independent reader's
    complete raw ledger, a mandatory future prerequisite, not in this math core.
    """
    require(len(context_ids)==len(set(context_ids))==1000,'one full original cohort')
    require(set(human_grid)==set(MODELS) and set(pair_grid)==set(JUDGES),'all original axes')
    human_facts={};model_facts={j:{} for j in JUDGES};cells={j:{} for j in JUDGES}
    for m in MODELS:
        require(set(human_grid[m])==set(ATTRS),'human seven attrs')
        hf={}
        for a in ATTRS:
            raw=human_grid[m][a];require(len(raw)==1000,'human full cohort slots');v=[_value(x) for x in raw];good=[x for x in v if x is not None]
            hf[a]=dict(mean=mean(good),n_valid=len(good),valid_mask_hex_little_endian=mask_hex([x is not None for x in v]),out_of_rubric_count=sum(not 1<=x<=5 for x in good))
        hf['average7']=mean([hf[a]['mean'] for a in ATTRS]) if all(hf[a]['mean'] is not None for a in ATTRS) else None;human_facts[m]=hf
    for j in JUDGES:
        require(set(pair_grid[j])==set(ATTRS),'judge seven attrs')
        for a in ATTRS:
            require(set(pair_grid[j][a])==set(MODELS),'all ten response source slots')
            masks={};means={};allh=[];alll=[];included=[m for m in MODELS if m!=EXCLUDED[j]]
            for m in MODELS:
                raw=pair_grid[j][a][m];require(len(raw)==1000,'all context slots retained');mask=[];h=[];l=[]
                for pair in raw:
                    require(type(pair) in (tuple,list) and len(pair)==2,'paired parsed slot');x,y=map(_value,pair);valid=x is not None and y is not None;mask.append(valid)
                    if valid:h.append(x);l.append(y)
                masks[m]=mask_hex(mask);means[m]=dict(human=mean(h),llm=mean(l),n_pairs=len(h))
                model_facts[j].setdefault(m,{})[a]=dict(unpaired_llm_mean=mean([p[1] for p in raw if p[1] is not None]),paired_human_mean=mean(h),paired_llm_mean=mean(l),n_pairs=len(h),paired_mask_hex_little_endian=masks[m])
                if m in included:allh.extend(h);alll.extend(l)
            v=dict(n_models=9,included_models=included,excluded_model=EXCLUDED[j],paired_masks_hex_little_endian={m:masks[m] for m in included},all10_model_pair_masks=masks,all10_model_pair_means=means,paired_error=paired_error(allh,alll))
            h=[means[m]['human'] for m in included];l=[means[m]['llm'] for m in included]
            if all(x is not None for x in h+l):
                v.update(anova_icc(h,l));v.update(equal_weight_human_mean=mean(h),equal_weight_llm_mean=mean(l),equal_weight_bias=mean([y-x for x,y in zip(h,l)]));v['normalized_abs_equal_weight_bias']=abs(v['equal_weight_bias'])/4;v['bootstrap']=bootstrap(h,l,design)
                c=v['bootstrap']['c1'];v['c1_ci_width']=interval_width(c['lower'],c['upper']);width=v['c1_ci_width'];v['width_status']=None if width is None else ('GR' if width<=.355 else 'MR' if width<=.560 else 'PR')
            else:
                v.update(icc_c1=None,icc_a1=None,msr=None,msc=None,anova_mse=None,equal_weight_human_mean=None,equal_weight_llm_mean=None,equal_weight_bias=None,normalized_abs_equal_weight_bias=None,bootstrap=None,c1_ci_width=None,width_status=None,reason='one or more required models has zero valid pairs; no silent model dropping')
            cells[j][a]=v
        for m in MODELS:
            xs=[model_facts[j][m][a]['unpaired_llm_mean'] for a in ATTRS];model_facts[j][m]['average7']=mean(xs) if all(x is not None for x in xs) else None
    return dict(schema='P165_INDEPENDENT_CORE_FACTS001',human_reference_model_facts=human_facts,judge_model_facts=model_facts,all28_cells=cells,shared_bootstrap_seed_index_design=design,complete1000_context_ids=context_ids,source_methods='ROOT921; independently derived fsum residual-form ANOVA, rawpair centered sums, linear percentile',no_automatic_scientific_credit=True)

def fixed_contrast_operands(facts):
    """Reports actual operands and literal thresholds, never auto-awards a paper.

    ROOT921's near-scale/weak-boundary interpretation remains an external fixed
    role. No near override, best sensitivity or changed threshold is selected.
    """
    rows=[]
    def add(name,value,threshold):
        rows.append(dict(id=name,value=value,threshold=threshold,literal_ge=None if value is None else value>=threshold))
    hm={m:facts['human_reference_model_facts'][m]['average7'] for m in MODELS[:-1]}
    opened=('ds_llama','ds_qwen','llama_3','qwen_2','qwen_3');closed=('claude','gemini','gpt4o','gpt4omini')
    if all(v is not None for v in hm.values()):
        add('RQ1_bestclosed_minus_bestopen',max(hm[m] for m in closed)-max(hm[m] for m in opened),.10)
        add('RQ1_Llama_minus_nextopen',hm['llama_3']-max(hm[m] for m in opened if m!='llama_3'),.15)
        add('RQ1_Qwen3_lowest_margin',min(hm[m] for m in hm if m!='qwen_3')-hm['qwen_3'],0)
    else:
        for n,t in [('RQ1_bestclosed_minus_bestopen',.10),('RQ1_Llama_minus_nextopen',.15),('RQ1_Qwen3_lowest_margin',0)]:add(n,None,t)
    for j in JUDGES:
        c=facts['all28_cells'][j]
        def avg(attrs,key):
            v=[c[a][key] for a in attrs];return mean(v) if all(x is not None for x in v) else None
        good=avg(('Guidance','Informativeness'),'icc_c1');weak=avg(('Relevance','Safety'),'icc_c1');add(j+'.RQ2_cognitive_vs_safety',good-weak if good is not None and weak is not None else None,.10)
        x,y=c['Empathy']['icc_c1'],c['Empathy']['icc_a1'];add(j+'.RQ2_empathy_scale_mismatch',x-y if x is not None and y is not None else None,.20)
        narrow=avg(('Guidance','Informativeness'),'c1_ci_width');wide=avg(('Relevance','Safety'),'c1_ci_width');add(j+'.RQ2_precision_difference',wide-narrow if wide is not None and narrow is not None else None,.15)
        for a,t in [('Empathy',.40),('Helpfulness',.30)]:add(j+'.RQ3_'+a+'_inflation',c[a]['paired_error']['bias'],t)
    return rows
