"""Independent stdlib CSV reduction. Definition-only until reviewed ROOT programme calls it.

Derivation: count the frozen author-status indicator over the complete CSV Cartesian
roster, then transpose that same full indicator into every source-defined margin.
This module never imports the primary reducer, executes its source, or recollects facts.
"""
from pathlib import Path
from fractions import Fraction
import csv,datetime as dt,hashlib,json

def pin(path):
 p=Path(path);b=p.read_bytes()
 return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(ref):
 if pin(ref['path'])!=ref:raise ValueError(('Whole source/input changed',ref['path']))
 return Path(ref['path'])
def load(ref):return json.loads(verify(ref).read_text(encoding='utf-8'))
def prefix_code(text,code):
 """Literal leading code plus explicit separator, never a whole-cell substring rule."""
 n=len(code)
 return text[:n].casefold()==code and (len(text)==n or text[n].isspace()or text[n]in'.,;:(')
def classify(raw,pointer,qualified_rules):
 if type(raw)is not str:raise TypeError(('Non-string raw CSV cell',pointer))
 t=raw.strip()
 if prefix_code(t,'none found'):
  suffix=t[len('none found'):].strip()
  if suffix not in ('','.',';'):
   witness=qualified_rules.get(pointer)
   if not witness or hashlib.sha256(raw.encode('utf-8')).hexdigest()!=witness['raw_UTF8_SHA256']:
    raise ValueError(('Qualified marker lacks independent exact-cell review',pointer))
   return 'AUTHOR_NONE_FOUND_WITH_RETAINED_QUALIFICATION'
  return 'AUTHOR_NONE_FOUND_STANDALONE'
 for code,label in [('not applicable','AUTHOR_NOT_APPLICABLE'),('not available','GUIDE_CONFIRMED_INFORMATION_ABSENCE'),('none','AUTHOR_CONFIRMED_ABSENCE'),('unsure','AUTHOR_UNCERTAINTY'),('todo','AUTHOR_INCOMPLETE_TODO')]:
  if prefix_code(t,code):return label
 return 'RETAINED_OTHER_LITERAL_CONTENT'if t else'UNRESOLVED_BLANK'
def embedded_marker(raw):
 """Independent character scan for the API's whole-word none + whitespace + found."""
 s=raw.casefold()
 def word(c):return c.isalnum()or c=='_'
 for i in range(max(0,len(s)-3)):
  if s[i:i+4]!='none'or i>0 and word(s[i-1]):continue
  j=i+4
  if j==len(s)or not s[j].isspace():continue
  while j<len(s)and s[j].isspace():j+=1
  if s[j:j+5]=='found'and (j+5==len(s)or not word(s[j+5])):return True
 return False
def pointer_part(s):return s.replace('~','~0').replace('/','~1')
def parse_csv(path):
 with Path(path).open(encoding='utf-8-sig',newline='')as f:rows=list(csv.reader(f))
 if len(rows)!=32 or any(len(row)!=46 for row in rows):raise ValueError('Exact two headers plus30 complete46-column CSV records')
 if rows[1][0]!='Agent':raise ValueError('Literal Agent header required')
 active=None;fields=[]
 for col in range(1,46):
  if rows[0][col]:active=rows[0][col]
  if active is None or not rows[1][col]:raise ValueError('Missing source section/field header')
  fields.append((active,rows[1][col]))
 if len(set(fields))!=45 or len({row[0]for row in rows[2:]})!=30:raise ValueError('Unique whole field/agent roster')
 return fields,rows[2:]
def strict_equal(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys()and all(strict_equal(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b)and all(strict_equal(x,y)for x,y in zip(a,b))
 return a==b
def summarize(cells,ordinals,key):
 picked=[cells[i-1]for i in ordinals]
 p=[c['none_found']for c in picked];w=[c['whole_cell_only_sensitivity']for c in picked];b=[c['broader_marker_sensitivity']for c in picked]
 return dict(key=key,cell_ordinals1=ordinals,primary_flags=p,literal_whole_cell_flags=w,broader_marker_flags=b,missing=p.count(True),denominator=len(ordinals),literal_whole_cell_missing=w.count(True),broader_marker_missing=b.count(True))
def csv_result(cfg):
 for k in ['execution_authorized','ROOT_source_and_criteria_reviewed','complete_original_transparency_reduction_authorized','parent_deadline_resources_output_enforced']:
  if cfg.get(k)is not True:raise PermissionError('Inert source-only independent CSV analysis')
 if cfg.get('schema')!='AI_AGENT_INDEX_COMPLETE_TRANSPARENCY029':raise ValueError('Exact current programme required')
 deadline=dt.datetime.fromisoformat(cfg['absolute_deadline_UTC'])
 if dt.datetime.now(dt.timezone.utc)>=deadline:raise TimeoutError('Existing parent inclusive deadline')
 for ref in cfg['whole_source_refs']:verify(ref)
 if pin(__file__)!=cfg['independent_source_ref']:raise ValueError('Executed independent source not current pin')
 verify(cfg['ROOT258_scope_decision_ref'])
 contract=load(cfg['matrix_contract_ref']);evidence=load(cfg['all1350_source_evidence_map_ref']);review=load(cfg['independent_semantic_review_ref'])
 if review.get('independent_all1350_source_semantics_and_format_join_passed')is not True:raise ValueError('Complete pre-outcome semantic review required')
 for k in ['original_JSON_ref','original_CSV_ref','matrix_contract_ref','all1350_source_evidence_map_ref','ROOT258_scope_decision_ref']:
  if review.get(k)!=cfg[k]:raise ValueError(('Exact semantic review/current input join',k))
 qualified=review['independently_reviewed_qualified_markers']
 header,rows=parse_csv(verify(cfg['original_CSV_ref']))
 agents=[r[0]for r in rows];fields=contract['all45_ordered_fields']
 if agents!=contract['all30_agent_order']or header!=[(f['section'],f['field'])for f in fields]:raise ValueError('CSV source roster differs from exact contract')
 source=evidence['all1350_ordered_cell_records']
 if len(source)!=1350:raise ValueError('Complete1350 source evidence required')
 cells=[];margins={'agent':{},'field':{},'section':{},'status':{}}
 for a,row in enumerate(rows):
  for f,(section,field)in enumerate(header):
   i=a*45+f;raw=row[f+1];p='/'+str(a)+'/'+pointer_part(section)+'/'+pointer_part(field);h=hashlib.sha256(raw.encode('utf-8')).hexdigest();tag=classify(raw,p,qualified);w=source[i]
   if (w['source_pointer'],w['agent_name'],w['agent_ordinal1'],w['section'],w['field'],w['raw_value'],w['source_raw_UTF8_SHA256'],w['prospective_author_status'])!=(p,row[0],a+1,section,field,raw,h,tag):raise ValueError(('Complete independent cell/source identity',p))
   c=dict(cell_ordinal1=i+1,agent_ordinal1=a+1,field_ordinal1=f+1,agent_name=row[0],section=section,field=field,source_pointer=p,raw_value=raw,source_raw_UTF8_SHA256=h,author_status=tag,none_found=tag in('AUTHOR_NONE_FOUND_STANDALONE','AUTHOR_NONE_FOUND_WITH_RETAINED_QUALIFICATION'),whole_cell_only_sensitivity=raw.strip().casefold()=='none found',broader_marker_sensitivity=embedded_marker(raw),individual_qualification_rationale=w['individual_qualification_rationale'],literal_any_information_semantics_ambiguous=w['literal_any_information_semantics_ambiguous'],known_cross_agent_reference_inconsistency=w['known_cross_agent_reference_inconsistency'])
   cells.append(c)
   for dimension,key in [('agent',row[0]),('field',f+1),('section',section),('status',tag)]:margins[dimension].setdefault(key,[]).append(i+1)
 safety_columns=[f for f,pair in enumerate(header)if pair[0]=='Safety, evaluation & impact']
 if len(safety_columns)!=8 or [header[f][1]for f in safety_columns]!=contract['eight_safety_fields']:raise ValueError('Whole eight-field safety domain')
 safe_ord=[a*45+f+1 for a in range(30)for f in safety_columns];safe_set=set(safe_ord)
 def summaries(dimension,only_safety=False):
  return [summarize(cells,[i for i in ids if not only_safety or i in safe_set],k)for k,ids in margins[dimension].items()]
 whole=summarize(cells,list(range(1,1351)),'whole');safe=summarize(cells,safe_ord,'safety')
 fig3={k:whole[k]for k in ['missing','denominator','literal_whole_cell_missing','broader_marker_missing']}
 fig3.update(complete_30x45_primary_flags=[[cells[a*45+f]['none_found']for f in range(45)]for a in range(30)],per_agent=summaries('agent'),per_field=summaries('field'),per_section=summaries('section'))
 category_col=header.index(('Product overview','Category'))+1;cohorts=[]
 for category,size in [('Enterprise',13),('Browser',5),('Chat',12)]:
  members=[a for a,row in enumerate(rows)if row[category_col]==category]
  if len(members)!=size:raise ValueError(('Frozen full cohort units',category))
  ids=[a*45+f+1 for a in members for f in safety_columns];entry=summarize(cells,ids,category);entry['members']=[agents[a]for a in members];cohorts.append(entry)
 if any(row[category_col]not in['Enterprise','Browser','Chat']for row in rows):raise ValueError('Unassigned source cohort')
 fig6={k:safe[k]for k in ['missing','denominator','literal_whole_cell_missing','broader_marker_missing']}
 safety_per_fields=[summarize(cells,[a*45+f+1 for a in range(30)],header[f][1])for f in safety_columns]
 fig6.update(complete_30x8_primary_flags=[[cells[a*45+f]['none_found']for f in safety_columns]for a in range(30)],per_agent=summaries('agent',True),per_field=safety_per_fields,cohorts=cohorts)
 checks=[]
 for name,n,d,tn,td in [('Fig3_all1350',whole['missing'],1350,198,1350),('Fig6_all240',safe['missing'],240,133,240)]:
  checks.append(dict(id=name,numerator=n,denominator=d,target_numerator=tn,target_denominator=td,passed=n==tn and d==td))
 for c,(tn,td,display)in zip(cohorts,[(67,104,'64'),(25,40,'63'),(41,96,'43')]):
  n=c['missing'];d=c['denominator'];label=c['key'];v=int(display)
  checks.append(dict(id='Fig6_'+label,numerator=n,denominator=d,target_numerator=tn,target_denominator=td,passed=n==tn and d==td))
  checks.append(dict(id='Fig6_'+label+'_percentage_display',numerator=n,denominator=d,percentage_exact_fraction=str(Fraction(100*n,d)),target_display=display,rounding_interval='[display-0.5,display+0.5) percent',passed=(2*v-1)*d<=200*n<(2*v+1)*d))
 caption=[]
 for label,n,d,display in [('Browser',67,104,'64'),('Enterprise',25,40,'63'),('Chat',41,96,'43')]:
  c=cohorts[['Enterprise','Browser','Chat'].index(label)]
  caption.append(dict(literal_category=label,literal_numerator=n,literal_denominator=d,literal_percentage_display=display,actual_numerator=c['missing'],actual_denominator=c['denominator'],literal_exact_fraction_passed=c['missing']==n and c['denominator']==d,role='MANDATORY_SUPPORTING_LITERAL_CAPTION_AUDIT_NOT_FULL'))
 result=dict(schema='AI_AGENT_INDEX_COMPLETE_TRANSPARENCY_RESULT029',source_mode='INDEPENDENT_ORIGINAL_CSV',original_input_ref=cfg['original_CSV_ref'],original_JSON_ref=cfg['original_JSON_ref'],original_CSV_ref=cfg['original_CSV_ref'],all1350_source_evidence_map_ref=cfg['all1350_source_evidence_map_ref'],matrix_contract_ref=cfg['matrix_contract_ref'],ROOT258_scope_decision_ref=cfg['ROOT258_scope_decision_ref'],all30_agent_order=agents,all45_ordered_fields=fields,all1350_cells=cells,Fig3=fig3,Fig6=fig6,all_source_status_classes=summaries('status'),primary_target_comparisons=checks,all_primary_published_targets_passed=all(x['passed']for x in checks),mandatory_literal_caption_audit=caption,all_literal_caption_audits_passed=all(x['literal_exact_fraction_passed']for x in caption),word_mean14=dict(role='HELD_AUXILIARY',published_text='14 words',computed=False,reason='Unreleased original tokenizer/markup/nonempty denominator generator'),all_other_original_fields_retained=True,all_other_paper_claims_reproduced=False,FULL_reproduction_qualified=False,paper_credit=0)
 extras=dict(exact_raw_cell_only_flags=[c['raw_value']=='None found'for c in cells],exact_raw_cell_only_role='Additional raw spelling sensitivity; never replaces primary or API normalized standalone sensitivity',all_qualified_source_semantics_ref=cfg['independent_semantic_review_ref'],all_qualified_or_mixed_cells_preserved=True,no_documentary_reannotation=True)
 extras['all1350_cohort_margins']=[]
 for category in ['Enterprise','Browser','Chat']:
  members={a for a,row in enumerate(rows)if row[category_col]==category};ids=[i for i in range(1,1351)if(i-1)//45 in members]
  extras['all1350_cohort_margins'].append(dict(cohort=category,complete_all45=summarize(cells,ids,category),by_section=[summarize(cells,[i for i in section_ids if i in set(ids)],section)for section,section_ids in margins['section'].items()],by_safety_field=[summarize(cells,[a*45+f+1 for a in sorted(members)],header[f][1])for f in safety_columns]))
 result['complete_cohort_cross_margins']=extras['all1350_cohort_margins']
 return result,extras
def save(path,value):
 with Path(path).open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+'\n')
 return pin(path)
def run_complete_independent(cfg,primary_result_ref):
 result,extras=csv_result(cfg);primary=load(primary_result_ref);api=load(cfg['result_API_ref']);fields=api['exact_comparison_fields']
 if primary.get('schema')!=result['schema']:raise ValueError('Exact primary result schema')
 comparisons=[dict(field=k,passed=strict_equal(result[k],primary[k]))for k in fields]
 for k in ['original_JSON_ref','original_CSV_ref','all1350_source_evidence_map_ref','matrix_contract_ref','ROOT258_scope_decision_ref']:
  comparisons.append(dict(field=k,passed=strict_equal(result[k],primary[k])))
 root=Path(cfg['scientific_output_root'])/'independent029';root.mkdir(parents=False,exist_ok=False)
 r=save(root/'COMPLETE_INDEPENDENT_CSV_TRANSPARENCY_RSTAT001.json',result)
 audit=dict(schema='AI_INDEX_COMPLETE_CSV_INDEPENDENT_AUDIT_RSTAT001',independent_source_ref=cfg['independent_source_ref'],primary_result_ref=primary_result_ref,independent_result_ref=r,all_required_comparison_fields=fields,complete_exact_field_comparisons=comparisons,all_complete_arrays_and_statuses_agree=all(x['passed']for x in comparisons),all_primary_published_targets_passed=result['all_primary_published_targets_passed'],complete_central_numeric_candidate=all(x['passed']for x in comparisons)and result['all_primary_published_targets_passed'],mandatory_literal_caption_audit=result['mandatory_literal_caption_audit'],extra_source_audits=extras,paper_credit=0,no_FULL_claim=True)
 ar=save(root/'COMPLETE_INDEPENDENT_CSV_AUDIT_RSTAT001.json',audit)
 if dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat(cfg['absolute_deadline_UTC']):raise TimeoutError('Parent deadline includes full independent result/audit writes')
 return dict(result_ref=r,audit_ref=ar,all_complete_arrays_and_statuses_agree=audit['all_complete_arrays_and_statuses_agree'],complete_central_numeric_candidate=audit['complete_central_numeric_candidate'],paper_credit=0)

if __name__=='__main__':raise SystemExit('Definition-only: ROOT-reviewed complete primary+independent programme required')
