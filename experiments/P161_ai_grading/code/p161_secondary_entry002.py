"""Complete separately authored P161 secondary route; dormant until ROOT grant.

Independence: Expat parsing and fsum moments/ANOVA/covariance/regression/ranks.
Only SciPy distribution tails and NumPy eigh are shared elementary primitives.
Never reads primary scores/results or imports primary mathematical code.
"""
from pathlib import Path
import hashlib,json,math,runpy

RATERS=('AI','Human-Z','Human-S')
PAIRS=(('AI_HumanZ','AI','Human-Z'),('AI_HumanS','AI','Human-S'),('HumanZ_HumanS','Human-Z','Human-S'))

def pin(path):
    p=Path(path);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def verify(ref):
    if pin(ref['path'])!=ref:raise ValueError('Changed complete secondary source/input '+ref['path'])
    return Path(ref['path'])

def write(path,value,guard):
    guard()
    with Path(path).open('x',encoding='ascii',newline='\n')as f:
        json.dump(value,f,ensure_ascii=True,allow_nan=False,separators=(',',':'));f.write('\n')
    guard();return pin(path)

def definitions(ref,name):return runpy.run_path(str(verify(ref)),run_name=name)

def undefined_paths(value,path=()):
    if value is None:return[dict(path=list(path),reason='Undefined under frozen estimator: zero variance/denominator, insufficient cases or unrecovered producer; no replacement value.')]
    if isinstance(value,float)and not math.isfinite(value):raise ValueError('No nonfinite JSON arithmetic value')
    if isinstance(value,dict):return[u for k,v in value.items()for u in undefined_paths(v,path+(k,))]
    if isinstance(value,list):return[u for i,v in enumerate(value)for u in undefined_paths(v,path+(i,))]
    return[]

def derive_complete(input_data,api,m,np,special,guard):
    rows=input_data['rows'];facts={};numerical_provenance={};null_reasons={}
    if len(rows)!=91 or[row['row']for row in rows]!=list(range(3,94)):raise ValueError('Whole original91/source row identity required')
    def add(identity,values):
        if identity in facts:raise ValueError('Duplicate independently derived fact ID')
        facts[identity]=values
    for campus in('All','UoC','AuT'):
        for r in RATERS:
            guard();x=[row['totals'][r]for row in rows if campus=='All'or row['University']==campus]
            a=m['descriptive'](x)
            add('DESC.'+campus+'.'+r,dict(n=a['n'],mean=a['mean'],sd=a['SD'],minimum=a['minimum'],maximum=a['maximum'],
                skewness=a['skewness_corrected'],kurtosis=a['kurtosis_corrected_excess'],raw_skewness=a['skewness_raw'],raw_excess_kurtosis=a['kurtosis_raw_excess']))
    for endpoint in tuple(str(i)for i in range(1,10))+('Total',):
        def value(row,r):return row['totals'][r]if endpoint=='Total'else row['criteria'][r][int(endpoint)-1]
        common=[row for row in rows if all(value(row,r)is not None for r in RATERS)]
        for label,ra,rb in PAIRS:
            guard();selected=[row for row in rows if value(row,ra)is not None and value(row,rb)is not None]
            x=[value(row,ra)for row in selected];y=[value(row,rb)for row in selected];ids=[row['row']for row in selected]
            c=m['correlations'](x,y,special);p=m['paired'](x,y,special)
            add('CORR.'+endpoint+'.'+label,dict(n=len(ids),case_rows=ids,pearson_r=c['pearson']['r'],pearson_p=c['pearson']['p'],
                spearman_rho=c['spearman_asymptotic']['r'],spearman_p=c['spearman_asymptotic']['p'],x_ranks=c['ranks_x'],y_ranks=c['ranks_y']))
            add('PAIRED.'+endpoint+'.'+label,dict(n=len(ids),case_rows=ids,mean_difference=p['mean_difference'],sd_difference=p['SD_difference'],
                t=p['t'],df=p['df'],p=p['p_two_tailed'],bonferroni_p=p['Bonferroni_p'],d=p['Cohen_d']))
            numerical_provenance['CORR.'+endpoint+'.'+label]=c
            numerical_provenance['PAIRED.'+endpoint+'.'+label]=p
            for mode,cases in(('common3',common),('pairwise',selected)):
                matrix=[[value(row,ra),value(row,rb)]for row in cases];a=m['icc_absolute_two_way'](matrix)
                key='ICC.'+mode+'.'+endpoint+'.'+label
                add(key,dict(n=a['n'],case_rows=[row['row']for row in cases],MSR=a['MS_rows'],MSC=a['MS_columns'],MSE=a['MS_error'],single=a['single'],average=a['average']))
                numerical_provenance[key]=dict(full_matrix=matrix,independent_ANOVA=a)
    for r in RATERS:
        guard();itemrows=[row['criteria'][r]for row in rows];keys=[row['row']for row in rows]
        alpha=m['alpha_variants'](itemrows,keys);pcas=m['pca_variants'](itemrows,keys,np)
        for mode in('listwise','pairwise'):
            a=alpha[mode];matrix=a['matrices'];caseids=matrix['listwise_case_keys']if mode=='listwise'else keys
            for kind in('raw','standardized'):
                add('ALPHA.'+r+'.'+kind+'_'+mode,dict(case_rows=caseids,pair_counts=matrix['pair_N'],
                    matrix=matrix['covariance'if kind=='raw'else'correlation'],alpha=a[kind]))
        for variant,p in pcas.items():
            add('PCA.'+r+'.'+variant,dict(case_rows=p['missingness']['matrix_case_keys'],pair_counts=p['missingness']['pair_N'],
                matrix=p['matrix'],eigenvalues=p['eigenvalues_descending'] if p['eigenvalues_descending'] is not None else [None]*9,
                percentages=p['explained_percent'] if p['explained_percent'] is not None else [None]*9))
        numerical_provenance['ALPHA.'+r]=alpha;numerical_provenance['PCA.'+r]=pcas
    for label,ra,rb in PAIRS:
        guard();selected=[row for row in rows if row['totals'][ra]is not None and row['totals'][rb]is not None]
        ids=[row['row']for row in selected];x=[row['totals'][ra]for row in selected];y=[row['totals'][rb]for row in selected]
        a=m['bland_altman'](x,y,special);b=m['kappa_all'](x,y)
        add('BA.'+label,dict(n=len(ids),case_rows=ids,x=a['x_pair_mean'],y=a['y_AI_minus_human'],mean_bias=a['mean_bias'],
            sd_difference=a['SD_difference'],loa_low=a['LOA_lower'],loa_high=a['LOA_upper'],intercept=a['intercept'],slope=a['slope'],
            slope_p=a['slope_p'],r_squared=a['R2'],fitted=a['fitted'] if a['fitted'] is not None else [None]*len(ids),
            residuals=a['residuals'] if a['residuals'] is not None else [None]*len(ids)))
        add('BANDS.'+label,dict(n=len(ids),case_rows=ids,x_categories=b['categories_x'],y_categories=b['categories_y'],table=b['counts'],
            exact_percent=b['exact_percent'],one_category_percent=b['exactly_one_percent'],two_plus_percent=b['two_or_more_percent']))
        occupied=[sum(v>0 for v in b[k]) for k in ('row_margins','column_margins')]
        degenerate=any(n<=1 for n in occupied)
        diagnostic_reason='Regular normal test inapplicable: an exact integer category margin occupies at most one category; raw coefficient/agreements/variance lineage is preserved without thresholding.'
        b['shared_diagnostic_semantics']=dict(occupied_integer_margin_categories=occupied,regular_normal_test_inapplicable=degenerate,
            reason=diagnostic_reason if degenerate else None,raw_variance_fields_retained=True)
        for variant,q in b['kappa'].items():
            identity='KAPPA.'+label+'.'+variant
            add(identity,dict(coefficient=q.get('coefficient'),observed_agreement=q.get('observed_agreement'),expected_agreement=q.get('expected_agreement'),
                delta_SE_diagnostic=None if degenerate else q.get('observed_delta_SE'),
                null_SE_diagnostic=None if degenerate else q.get('null_independence_SE'),
                normal_p_diagnostic=None if degenerate else q.get('null_normal_p')))
            if degenerate:null_reasons[identity]=diagnostic_reason
        numerical_provenance['BA.'+label]=a;numerical_provenance['BANDS_KAPPA.'+label]=b
    for label,raters in(('AI_HumanZ',('AI','Human-Z')),('AI_HumanS',('AI','Human-S')),('All3',RATERS)):
        for center in('mean','median'):
            guard();groups=[[row['totals'][r]for row in rows if row['totals'][r]is not None]for r in raters]
            a=m['levene'](groups,special,center)
            add('LEVENE.'+label+'.'+center,dict(group_sizes=a['group_N'],centers=a['centers'],absolute_deviations=a['transformed'],F=a['F'],df1=a['df1'],df2=a['df2'],p=a['p']))
            numerical_provenance['LEVENE.'+label+'.'+center]=a
    for r in RATERS:
        guard();x=[row['totals'][r]for row in rows];b=m['reconstructed_boxplot'](x);h=m['reconstructed_density'](x)
        add('FIGURE1.'+r,dict(values=x,q1=b.get('q1'),median=b.get('median'),q3=b.get('q3'),whisker_low=b.get('lower_whisker'),whisker_high=b.get('upper_whisker'),outliers=b.get('outliers')))
        for figure in('FIGURE2','FIGURE3'):
            add(figure+'.'+r,dict(values=x,bin_edges=h['bin_edges'],counts=h['counts'],density=h['histogram_density'],kde_x=h['KDE_grid'],kde_y=h['KDE_density'] if h['KDE_density'] is not None else [None]*len(h['KDE_grid'])))
        numerical_provenance['FIGURE1.'+r]=b;numerical_provenance['FIGURE2_3.'+r]=h
    expected=[q['id']for q in api['ordered_fact_queries']]
    if len(facts)!=189 or set(expected)!=set(facts):raise ValueError('Every whole189 ordered fact required; no extra/missing query')
    out=[]
    for q in api['ordered_fact_queries']:
        values=facts[q['id']]
        if set(values)!=set(q['fields']):raise ValueError('Whole field schema mismatch '+q['id'])
        ordered={k:values[k]for k in q['fields']}
        unknown=undefined_paths(ordered)
        if q['id'] in null_reasons:
            for u in unknown:
                if u['path'] in [['delta_SE_diagnostic'],['null_SE_diagnostic'],['normal_p_diagnostic']]:u['reason']=null_reasons[q['id']]
        out.append(dict(id=q['id'],values=ordered,undefined=unknown))
    return out,numerical_provenance

def run_complete_secondary(cfg,numpy_module,special_module,caller_guard):
    if any(cfg.get(k)is not True for k in('execution_authorized','ROOT_full_P161_science_authorized','ROOT_P161_current_source_review_passed')):raise PermissionError('P161 secondary remains dormant')
    schema=json.loads(verify(cfg['facts_schema_ref']).read_bytes())
    verify(cfg['query_roles_ref']);verify(cfg['root_design340_ref'])
    if set(schema.get('figure_fact_bindings',{}))!={'1','2','3','4','5'}:raise ValueError('Frozen whole-five-figure API002 required')
    m=definitions(cfg['secondary_primitives_ref'],'INDEPENDENT_P161_FSUM_DEFINITIONS')
    parser=definitions(cfg['secondary_parser_ref'],'INDEPENDENT_P161_EXPAT_DEFINITIONS')
    output=Path(cfg['output_root'])/'secondary002';output.mkdir(exist_ok=False)
    data,raw=parser['read_complete_workbook'](cfg['workbook_ref'],caller_guard)
    provenance_ref=write(output/'ORIGINAL_XML_LITERAL_PROVENANCE_SECONDARY002.json',raw,caller_guard)
    facts,extra=derive_complete(data,schema,m,numpy_module,special_module,caller_guard)
    result=dict(schema='P161_COMPLETE_FACTS001',route='SECONDARY',input=data,facts=facts,not_run=schema['declared_not_run_variants'])
    numerical_ref=write(output/'COMPLETE_INDEPENDENT_NUMERICAL_LINEAGE002.json',dict(values=extra,undefined=undefined_paths(extra)),caller_guard)
    result_ref=write(output/'COMPLETE_FACTS.json',result,caller_guard)
    return dict(result_ref=result_ref,fact_count=len(facts),provenance_ref=provenance_ref,numerical_lineage_ref=numerical_ref,
        no_whole_family_or_paper_credit_claimed=True)
