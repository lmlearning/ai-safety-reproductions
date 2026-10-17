"""Complete publication/integrity/field audit after both independent routes.

Literal query metadata are shared; no primary reduction is called. This file
does not open scores or calculate estimators at import or during preparation.
"""
from decimal import Decimal
import math

def at(value,path):
    for p in path:value=value[p]
    return value

def rounded(value,literal):
    d=Decimal(literal);u=Decimal(1).scaleb(d.as_tuple().exponent)
    return interval(value,dict(kind='PRINTED_ROUND_HALF_UNIT_REFERENCE',lower=str(d-u/2),upper=str(d+u/2)))

def interval(value,ref):
    if value is None:return dict(value=None,passed=False,status='UNDEFINED')
    if isinstance(value,bool)or not isinstance(value,(int,float))or not math.isfinite(value):raise ValueError('Finite real publication statistic required')
    d=Decimal.from_float(value)if isinstance(value,float)else Decimal(value)
    if ref['kind']=='EXACT_INTEGER':passed=d==Decimal(ref['value'])
    elif ref['kind']=='STRICT_UPPER_BOUND':passed=d>=Decimal(ref.get('lower','0'))and d<Decimal(ref['upper'])
    elif ref['kind']=='PRINTED_ROUND_HALF_UNIT_REFERENCE':
        margin=Decimal(ref.get('float_margin','0'))
        if not Decimal(0)<=margin<=Decimal('1e-12'):raise ValueError('Unreviewed printed rounding margin')
        low=Decimal(ref['lower'])-margin;high=Decimal(ref['upper'])+margin
        passed=(d>=low if ref.get('lower_inclusive',True)else d>low)and(d<=high if ref.get('upper_inclusive',True)else d<high)
    else:raise ValueError('Unknown frozen publication reference')
    return dict(value=value,passed=bool(passed),status='PASS'if passed else'FAIL')

def tree_compare(a,b,path,rows,exact=False):
    if isinstance(a,dict)and isinstance(b,dict):
        keys=sorted(set(a)|set(b));rows.append(dict(path=path,kind='DICTIONARY_KEYS',passed=set(a)==set(b)))
        for k in keys:
            if k not in a or k not in b:rows.append(dict(path=path+[k],kind='MISSING_FIELD',passed=False));continue
            tree_compare(a[k],b[k],path+[k],rows,exact)
    elif isinstance(a,list)and isinstance(b,list):
        rows.append(dict(path=path,kind='LIST_LENGTH',primary=len(a),secondary=len(b),passed=len(a)==len(b)))
        for i,(x,y)in enumerate(zip(a,b)):tree_compare(x,y,path+[i],rows,exact)
    else:
        if isinstance(a,bool)or isinstance(b,bool):ok=type(a)is type(b)and a==b;kind='EXACT_BOOLEAN'
        elif isinstance(a,(int,float))and isinstance(b,(int,float)):
            if not math.isfinite(a)or not math.isfinite(b):raise ValueError('Nonfinite result leaf')
            strict=exact or type(a)is int or type(b)is int
            ok=a==b if strict else abs(a-b)<=1e-10+1e-8*max(abs(a),abs(b));kind='EXACT_NUMERIC'if strict else'CONTINUOUS'
        else:ok=type(a)is type(b)and a==b;kind='EXACT_LITERAL_OR_NULL'
        rows.append(dict(path=path,kind=kind,primary=a,secondary=b,passed=bool(ok)))

def nulls(value,path=()):
    if value is None:return[tuple(path)]
    if isinstance(value,float)and not math.isfinite(value):raise ValueError('NaN/Inf result forbidden')
    if isinstance(value,dict):return[p for k,v in value.items()for p in nulls(v,path+(k,))]
    if isinstance(value,list):return[p for i,v in enumerate(value)for p in nulls(v,path+(i,))]
    return[]

def validate_result(result,api):
    if result['schema']!='P161_COMPLETE_FACTS001'or set(result['input'])!={'rows'}:raise ValueError('Complete facts/input schema required')
    expected=api['ordered_fact_queries'];facts=result['facts']
    if len(facts)!=189 or[f['id']for f in facts]!=[q['id']for q in expected]:raise ValueError('Exact all189 fact ordering required')
    for f,q in zip(facts,expected):
        if set(f['values'])!=set(q['fields']):raise ValueError('Exact whole fact field roster required')
        paths=[tuple(x['path'])for x in f['undefined']]
        if len(paths)!=len(set(paths))or set(paths)!=set(nulls(f['values']))or any(not x['reason']for x in f['undefined']):raise ValueError('Every undefined leaf needs exactly one explicit reason')
    if[x['id']for x in result['not_run']]!=[x['id']for x in api['declared_not_run_variants']]:raise ValueError('All unresolved methods retained')
    if any(not x['reason']for x in result['not_run']):raise ValueError('Unresolved method reason missing')

def compare_complete(primary,secondary,api,guard):
    validate_result(primary,api);validate_result(secondary,api);ledger=[]
    tree_compare(primary['schema'],secondary['schema'],['schema'],ledger,True)
    tree_compare(primary['input'],secondary['input'],['input'],ledger,True)
    for a,b in zip(primary['facts'],secondary['facts']):
        guard();tree_compare(a['id'],b['id'],['facts',a['id'],'id'],ledger,True)
        tree_compare(a['values'],b['values'],['facts',a['id'],'values'],ledger)
        # Undefined paths must agree; different explanatory prose remains visible
        # in both original files but is not a mathematical disagreement.
        pa=sorted((list(x['path'])for x in a['undefined']),key=repr);pb=sorted((list(x['path'])for x in b['undefined']),key=repr)
        tree_compare(pa,pb,['facts',a['id'],'undefined_paths'],ledger,True)
    tree_compare([x['id']for x in primary['not_run']],[x['id']for x in secondary['not_run']],['not_run_ids'],ledger,True)
    return dict(all_complete_fields_agree=all(x['passed']for x in ledger),comparisons=ledger,
        comparisons_count=len(ledger),failures_count=sum(not x['passed']for x in ledger),
        continuous_rule='abs1e-10+rel1e-8; exact if either leaf integer; input/formula values exact',
        independent_neural_or_historical_rating_collection_claim=False)

def integrity(result,source_schema):
    rows=result['input']['rows'];facts={f['id']:f['values']for f in result['facts']};checks=[]
    def c(name,passed,details=None):checks.append(dict(id=name,passed=bool(passed),details=details))
    c('ALL91_SOURCE_ROWS',[r['row']for r in rows]==list(range(3,94)))
    expected=source_schema['all91_rows_in_source_order']
    identity=[dict(row=x['worksheet_row1'],AA=x['original_ID_fields']['AA']['literal'],AAUni=x['original_ID_fields']['AA_Uni']['literal'],University=x['original_ID_fields']['University']['literal'])for x in expected]
    actual=[{k:r[k]for k in('row','AA','AAUni','University')}for r in rows]
    c('EXACT_ORIGINAL_ALL_ID_AND_CAMPUS_FIELDS',actual==identity)
    raters=('AI','Human-Z','Human-S');pairs={'AI_HumanZ':('AI','Human-Z'),'AI_HumanS':('AI','Human-S'),'HumanZ_HumanS':('Human-Z','Human-S')}
    c('ALL27_CRITERION_FIELDS',all(set(r['criteria'])==set(raters)and all(len(r['criteria'][k])==9 for k in raters)for r in rows))
    formula=[dict(row=r['row'],rater=k,audit=r['formula_audits'][k])for r in rows for k in raters]
    c('ALL273_CACHED_TOTAL_FORMULAS_EXACT',len(formula)==273 and all(x['audit']['cache_equal']is True for x in formula),formula)
    c('ALL91_CACHED_TOTALS_PRESERVED',all(set(r['totals'])==set(raters)and all(isinstance(r['totals'][k],(int,float))and not isinstance(r['totals'][k],bool)and math.isfinite(r['totals'][k])for k in raters)for r in rows))
    for endpoint in tuple(str(i)for i in range(1,10))+('Total',):
        value=lambda r,k:r['totals'][k]if endpoint=='Total'else r['criteria'][k][int(endpoint)-1]
        common=[r['row']for r in rows if all(value(r,k)is not None for k in raters)]
        targetN=90 if endpoint=='6'else 91
        c('COMMON3_N_'+endpoint,len(common)==targetN,common)
        for pair,(a,b)in pairs.items():
            own=[r['row']for r in rows if value(r,a)is not None and value(r,b)is not None]
            for mask,ids in(('common3',common),('pairwise',own)):
                v=facts['ICC.'+mask+'.'+endpoint+'.'+pair]
                c('EXACT_MASK_'+mask+'_'+endpoint+'_'+pair,v['case_rows']==ids and v['n']==len(ids))
                c('FINITE_BOTH_ICC_'+mask+'_'+endpoint+'_'+pair,all(isinstance(v[k],(int,float))and math.isfinite(v[k])for k in('single','average')))
    return dict(all_integrity_passed=all(x['passed']for x in checks),checks=checks,raw_cached_totals_never_repaired=True)

def publication_audit(result,roles,api,source_schema,guard):
    validate_result(result,api);facts={f['id']:f['values']for f in result['facts']};rows=result['input']['rows']
    target_rows=[]
    for q in roles['all155_table_plus6_abstract_targets']:
        guard();value=at(facts[q['query_id']],q['field_path']);verdict=interval(value,q['reference'])
        status='UNESTABLISHED_ORIGINAL_TEST'if q['query_id'].startswith('KAPPA.')and q['field_path']==['normal_p_diagnostic']else verdict['status']
        target_rows.append(dict(id=q['id'],role=q['role'],literal=q['original_literal'],query_id=q['query_id'],field_path=q['field_path'],
            reference=q['reference'],**verdict,source_verdict=status,method_identification=q.get('method_identification')))
    central=[q for q in target_rows if q['role'].startswith('CENTRAL_ICC')]
    if len(target_rows)!=161 or len(central)!=86:raise ValueError('All155table+6abstract and86central targets required')
    if any(q['reference'].get('upper_inclusive') is not False or q['reference'].get('lower_inclusive') is not True for q in central):raise ValueError('ROOT340 exact half-open central references required; historical tie prose is not operative')
    directions=[]
    for q in roles['central_ordering_queries']:
        hh=facts[q['HH_query']][q['metric_field']];ais=[facts[k][q['metric_field']]for k in q['AI_queries']]
        passed=hh is not None and all(x is not None and hh>x for x in ais)
        directions.append(dict(query=q,HH=hh,AI=ais,passed=passed))
    extra=[]
    for q in roles['complete_all27_extra_query_bindings']:
        guard();bindings=[]
        for b in q['query_bindings']:
            value=at(facts[b['query_id']],b['field_path']);bindings.append(dict(binding=b,**interval(value,q['source_target']['reference'])))
        if q.get('derived_binding'):
            b=q['derived_binding'];vals=[facts[k][b['field']]for k in b['queries']]
            value=None if any(v is None for v in vals)else(min(vals)if b['operation']=='minimum'else max(vals))*b['scale']
            bindings.append(dict(derived_binding=b,**interval(value,q['source_target']['reference'])))
        if q.get('structural_binding'):
            key=q['id'];domain=True
            if key=='DESIGN.N':value=len(rows)
            elif key=='DESIGN.UoC_N':value=sum(r['University']=='UoC'for r in rows)
            elif key=='DESIGN.AUTh_N':value=sum(r['University']=='AuT'for r in rows)
            elif key=='DESIGN.Criteria':value=9;domain=all(len(v)==9 for r in rows for v in r['criteria'].values())
            elif key=='DESIGN.Minimum_criterion':value=1;domain=all(v>=1 for r in rows for x in r['criteria'].values()for v in x if v is not None)
            elif key=='DESIGN.Maximum_criterion':value=10;domain=all(v<=10 for r in rows for x in r['criteria'].values()for v in x if v is not None)
            elif key=='DESIGN.Maximum_total':value=90;domain=all(v<=90 for r in rows for v in r['totals'].values())
            elif key=='F4.BA_LOA_multiplier':value=1.96
            else:raise ValueError('Unknown frozen structural binding '+key)
            check=interval(value,q['source_target']['reference']);check['passed']=check['passed']and domain
            bindings.append(dict(structural_binding=q['structural_binding'],domain_validation=domain,**check))
        extra.append(dict(id=q['id'],source_target=q['source_target'],all_declared_bindings=bindings,
            original_method_identification=q['original_method_identification'],source_verdict=q.get('source_verdict','Declared primary convention; variants are nonrescue; original option identity may remain unestablished.')))
    if len(extra)!=27:raise ValueError('All27 extra source targets required')
    semantic=[semantic_claim(q,facts)for q in roles['additive_full_semantic_claims']]
    if len(semantic)!=27:raise ValueError('All27 whole-paper semantic records required')
    figures=[]
    for n,ids in roles['figure_fact_bindings'].items():
        if any(i not in facts for i in ids):raise ValueError('A complete figure numerical family missing')
        figures.append(dict(figure=n,complete_fact_ids=ids,numeric_arrays_complete=True,
            original_producer='UNESTABLISHED',reconstruction_not_literal_published_graphic=True))
    integ=integrity(result,source_schema)
    core=all(q['passed']for q in central)and all(q['passed']for q in directions)and integ['all_integrity_passed']and len(figures)==5
    return dict(route=result.get('route'),all161_literal_table_and_abstract=target_rows,all86_central_passed=all(q['passed']for q in central),
        all20_directions=directions,all27_extras=extra,all27_semantic_claims=semantic,all5_figure_audits=figures,integrity=integ,
        complete_CENTRAL_candidate=bool(core),whole_paper_or_FULL_reproduced=False,all_support_required_to_be_reported_not_claimed_passed=True,paper_credit=0)

def semantic_claim(q,f):
    """All clauses retained. Underidentified words do not become invented gates."""
    key=q['id'];components=[];reason=None;qualified=False
    def check(label,value,literal):components.append(dict(component=label,literal=literal,**rounded(value,literal)))
    def pred(label,passed,values):components.append(dict(component=label,values=values,passed=bool(passed),status='PASS'if passed else'FAIL'))
    def val(identity,field):return f[identity][field]
    def extreme(ids,field,op):
        x=[val(i,field)for i in ids];return None if any(v is None for v in x)else op(x)
    ids=q['query_ids']
    if key in('ABSTRACT.CONSTRUCT_AND_HIGH_STAKES','INTERPRETATION.FAIRNESS_VALIDITY','CONCLUSION_AND_LIMITATIONS'):
        reason='Interpretation/causality/fairness/interchangeability not identified from the released scores.'
    elif key in('RESULTS.HH_P_VALUES',):reason='Original ICC significance-test producer not specified.'
    elif key=='METHODS.CAMPUS_DESCRIPTIVES':
        pred('Complete allcampus descriptives emitted',all(i in f for i in ids),ids);qualified=True;reason='No published campus numerical reference; complete descriptive audit only.'
    elif key in('ABSTRACT.SCORE_INFLATION','DISCUSSION.INFLATION'):
        for i,lit in zip(ids[:2],q['published_literals']):check(i,val(i,'mean_difference'),lit)
        if key=='DISCUSSION.INFLATION':reason='Poor discrimination is not an operationally defined numeric predicate; exact mean/SD facts remain retained.';qualified=True
    elif key=='ABSTRACT.VARIANCE_COMPRESSION':
        a=val('DESC.All.AI','sd');h=[val('DESC.All.'+r,'sd')for r in('Human-Z','Human-S')];pred('AI sampleSD below both humanSD',a is not None and all(v is not None and a<v for v in h),[a]+h)
    elif key=='ABSTRACT.PROPORTIONAL_BIAS':
        x=[val(i,'slope')for i in ids];pred('Both specified BA slopes negative',all(v is not None and v<0 for v in x),x)
    elif key in('ABSTRACT.KAPPA','RESULTS.BAND_BODY'):
        for i,lit in zip(('KAPPA.AI_HumanS.linear','KAPPA.AI_HumanZ.linear'),('.017','.367')):check(i,val(i,'coefficient'),lit)
        if key=='RESULTS.BAND_BODY':
            for p,e,t in [('AI_HumanS','40.7','5.5'),('AI_HumanZ','50.5','4.4')]:check(p+' exact',val('BANDS.'+p,'exact_percent'),e);check(p+'2plus',val('BANDS.'+p,'two_plus_percent'),t)
        reason='Exact original weighted-kappa p/SE is unestablished; diagnostic normal p never establishes the source test.';qualified=True
    elif key in('RESULTS.HH_ICC_RANGE','RESULTS.AI_Z_ICC_RANGE'):
        pair='HumanZ_HumanS'if key=='RESULTS.HH_ICC_RANGE'else'AI_HumanZ';ks=['ICC.common3.'+str(i)+'.'+pair for i in range(1,10)]
        literals=q['published_literals'];check('criterion single minimum',extreme(ks,'single',min),literals[0]);check('criterion single maximum',extreme(ks,'single',max),literals[1])
        if pair=='HumanZ_HumanS':check('criterion average minimum',extreme(ks,'average',min),literals[2]);check('criterion average maximum',extreme(ks,'average',max),literals[3])
        else:check('total single',val('ICC.common3.Total.'+pair,'single'),literals[2]);check('total average',val('ICC.common3.Total.'+pair,'average'),literals[3])
    elif key in('RESULTS.CORRELATION_RANGE','DISCUSSION.CORRELATION_RANGE'):
        check('minimum Pearson',extreme(ids,'pearson_r',min),q['published_literals'][0]);check('maximum Pearson',extreme(ids,'pearson_r',max),q['published_literals'][1])
    elif key=='RESULTS.PAIRED_ROUNDED':
        for p,lits in [('AI_HumanZ',['2.71','2.48','.015','.26']),('AI_HumanS',['3.32','2.63','.010','.28'])]:
            for field,lit in zip(('mean_difference','t','p','d'),lits):check(p+'.'+field,val('PAIRED.Total.'+p,field),lit)
        check('HH difference',val('PAIRED.Total.HumanZ_HumanS','mean_difference'),'.60');p=val('PAIRED.Total.HumanZ_HumanS','p');pred('HH nonsignificant',p is not None and p>=.05,p)
    elif key=='RESULTS.CRITERIA6_7_EFFECT':
        ds=[abs(val(i,'d'))for i in ids if val(i,'d')is not None];check('largest absolute paired d',max(ds)if ds else None,'.71')
        for pair in('AI_HumanZ','AI_HumanS'):
            ranking=sorted([(i,val('PAIRED.'+str(i)+'.'+pair,'mean_difference'))for i in range(1,10)],key=lambda x:abs(x[1])if x[1]is not None else-1,reverse=True)
            components.append(dict(component=pair+' complete mean-gap ranking',ranking=ranking,passed=None,status='UNESTABLISHED_AGGREGATION'))
        qualified=True;reason='Original meaning of largest acrossraters is not specified; fullperpair ranks and all18 effects retained without selecting a matching aggregation.'
    elif key=='RESULTS.AI_S_APPROXIMATE':
        criterion_ids=['ICC.common3.'+str(i)+'.AI_HumanS' for i in range(1,10)]
        for field,lit in [('single','.28'),('average','.44')]:
            values=[val(i,field) for i in criterion_ids]
            for identity,value in zip(criterion_ids,values):check(identity+'.'+field,value,lit)
            check('nine-criterion unweighted mean '+field,None if any(v is None for v in values)else math.fsum(values)/9,lit)
            check('total '+field,val('ICC.common3.Total.AI_HumanS',field),lit)
        qualified=True;reason='UNESTABLISHED_AVERAGING: source does not uniquely identify whether approximate ICC refers to a criterion average, each criterion, or total. All views retained; no matching-view rescue.'
    elif key=='RESULTS.HH_ABOVE_80':
        x=[val(i,'single')for i in ids];pred('Literal allHH single above.80',all(v is not None and v>.8 for v in x),x);reason='SOURCE_INTERNAL_CONSISTENCY_FAILED before outcomes: originalTable5 itself includes.782/.760/.754.';qualified=True
    elif key=='RESULTS.BA_R2_RANGE':check('minimum percentR2',None if extreme(ids,'r_squared',min)is None else 100*extreme(ids,'r_squared',min),'6');check('maximum percentR2',None if extreme(ids,'r_squared',max)is None else 100*extreme(ids,'r_squared',max),'9')
    elif key in('RESULTS.PCA_VARIANCE','FIGURE5.CAPTION_PC1_APPROX'):
        for r,lit in zip(('AI','Human-Z','Human-S'),q['published_literals'][:3]):check(r+'PC1',val('PCA.'+r+'.correlation_listwise','percentages')[0]if val('PCA.'+r+'.correlation_listwise','percentages')is not None else None,lit)
        if key=='RESULTS.PCA_VARIANCE':
            x=[val('PCA.'+r+'.correlation_listwise','percentages')for r in('Human-Z','Human-S')];pred('Literal graphical humanPC1above80',all(v is not None and len(v)>0 and v[0] is not None and isinstance(v[0],(int,float)) and math.isfinite(v[0]) and v[0]>80 for v in x),x)
        qualified=True;reason='Original PCA matrix/plot producer unestablished; all six fixed variants retained, with no anymatchingvariant claim.'
    elif key=='DISCUSSION.RELIABILITY_AND_ALPHA':
        values={i:f[i]for i in ids};components.append(dict(component='Complete source-referenced reliability values',values=values,passed=None,status='UNESTABLISHED_QUALIFIER'))
        qualified=True;reason='Approaching/rarely/high do not specify numeric thresholds or frequency; no invented predicate.'
    elif key=='DISCUSSION.BAND_40_51':
        check('minimum exactpercent strictliteral',extreme(ids,'exact_percent',min),'40');check('maximum exactpercent strictliteral',extreme(ids,'exact_percent',max),'51');qualified=True;reason='Strict printed endpoint checks retained; about qualifier has no recovered interval rule.'
    elif key=='RESULTS.DESCRIPTIVE_BODY':
        for r,lo,sk in [('AI','55','-.873'),('Human-Z','31','-1.628'),('Human-S','26','-1.549')]:check(r+'minimum',val('DESC.All.'+r,'minimum'),lo);check(r+'skewness',val('DESC.All.'+r,'skewness'),sk)
        check('AI SD',val('DESC.All.AI','sd'),'8.41');check('AI kurtosis',val('DESC.All.AI','kurtosis'),'.156')
        for r in('Human-Z','Human-S'):pred(r+'SDabove10.7',val('DESC.All.'+r,'sd')>10.7,val('DESC.All.'+r,'sd'));check(r+'kurtosis strictabout4.0',val('DESC.All.'+r,'kurtosis'),'4.0')
    elif key=='RESULTS.LEVENE_SIGNIFICANCE':
        for pair in('AI_HumanZ','AI_HumanS','All3'):
            for center in('mean','median'):
                p=val('LEVENE.'+pair+'.'+center,'p');pred(pair+'.'+center+'p<.05',p is not None and p<.05,p)
        qualified=True;reason='Original grouping/centering not identified. All declared tests retained; no anymatchingbranch proof.'
    elif key=='DISCUSSION.THRESHOLD_MISCLASSIFICATION':
        components=[dict(component=i,complete_4by4_table=f[i]['table'],passed=None,status='UNESTABLISHED_CLUSTER_PREDICATE')for i in ids];qualified=True;reason='No quantitative clustering statistic/cutoff stated; entire4x4tables retained.'
    else:raise ValueError('Missing mandatory semantic predicate '+key)
    passed=all(x.get('passed')is True for x in components)if components else False
    status='UNESTABLISHED'if reason or qualified else'PASS'if passed else'FAIL'
    return dict(source=q,components=components,strict_defined_components_passed=passed,verdict=status,reason=reason,
        no_anymatching_variant_rescue=True,not_a_central_gate=True)
