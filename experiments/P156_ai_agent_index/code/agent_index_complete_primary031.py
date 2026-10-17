"""Complete original30x45 author-coded transparency reduction; inert without ROOT authority."""
from pathlib import Path
from fractions import Fraction
import datetime as dt,hashlib,json,re,sys

def pin(p):
 p=Path(p).absolute()
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def load_ref(r):
 if pin(r['path'])!=r:raise ValueError(('Current complete source/input pin',r['path']))
 return json.loads(Path(r['path']).read_bytes())
def save(p,obj):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(obj,indent=2,ensure_ascii=True,allow_nan=False)+'\n')
 return pin(p)
def none_found_author_status(raw,source_cell):
 if not isinstance(raw,str):raise TypeError(('Nonstring original annotation',source_cell['source_pointer']))
 t=raw.strip();match=re.match(r'^None found(?=$|[\s.,;:(])',t,re.I)
 if match:
  rest=t[match.end():].strip()
  if rest and rest not in ['.',';']:
   if not source_cell['individual_qualification_rationale']:raise ValueError(('Qualified marker lacks frozen rationale',source_cell['source_pointer']))
   label='AUTHOR_NONE_FOUND_WITH_RETAINED_QUALIFICATION'
  else:label='AUTHOR_NONE_FOUND_STANDALONE'
 else:
  label='RETAINED_OTHER_LITERAL_CONTENT'
  for marker,kind in [('Not applicable','AUTHOR_NOT_APPLICABLE'),('Not available','GUIDE_CONFIRMED_INFORMATION_ABSENCE'),('None','AUTHOR_CONFIRMED_ABSENCE'),('UNSURE','AUTHOR_UNCERTAINTY'),('TODO','AUTHOR_INCOMPLETE_TODO')]:
   if re.match(r'^'+re.escape(marker)+r'(?=$|[\s.,;:(])',t,re.I):label=kind;break
  if not t:label='UNRESOLVED_BLANK'
 if label!=source_cell['prospective_author_status']:raise ValueError(('Current exact source status differs from frozen pre-outcome map',source_cell['source_pointer']))
 return label,bool(match)
def group_summary(cells,keys):
 # Preserve the full flag vectors and cell ordinals; no structural-zero row disappears.
 out=[]
 for key in keys:
  selected=[c for c in cells if c['group_key']==key]
  out.append(dict(key=key,cell_ordinals1=[c['cell_ordinal1']for c in selected],primary_flags=[c['none_found']for c in selected],literal_whole_cell_flags=[c['whole_cell_only_sensitivity']for c in selected],broader_marker_flags=[c['broader_marker_sensitivity']for c in selected],missing=sum(c['none_found']for c in selected),denominator=len(selected),literal_whole_cell_missing=sum(c['whole_cell_only_sensitivity']for c in selected),broader_marker_missing=sum(c['broader_marker_sensitivity']for c in selected)))
 return out
def primary_result(cfg):
 if any(cfg.get(k)is not True for k in ['execution_authorized','ROOT_source_and_criteria_reviewed','complete_original_transparency_reduction_authorized','parent_deadline_resources_output_enforced']):raise PermissionError('Inert source-only complete original transparency primary')
 if cfg['schema']!='AI_AGENT_INDEX_COMPLETE_TRANSPARENCY029':raise ValueError('Current exact protocol')
 if dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat(cfg['absolute_deadline_UTC']):raise TimeoutError('Existing parent inclusive deadline')
 for r in cfg['whole_source_refs']:
  if pin(r['path'])!=r:raise ValueError(('Whole current source changed',r['path']))
 if pin(cfg['ROOT258_scope_decision_ref']['path'])!=cfg['ROOT258_scope_decision_ref']:raise ValueError('Frozen ROOT258 scope')
 if pin(__file__)!=cfg['primary_source_ref']:raise ValueError('Current primary source')
 raw=load_ref(cfg['original_JSON_ref']);matrix=load_ref(cfg['matrix_contract_ref']);evidence=load_ref(cfg['all1350_source_evidence_map_ref'])
 if len(raw)!=30 or [r['agent_name']for r in raw]!=matrix['all30_agent_order']:raise ValueError('Complete original ordered30 agents')
 fields=matrix['all45_ordered_fields'];frozen=evidence['all1350_ordered_cell_records']
 if len(fields)!=45 or len(frozen)!=1350:raise ValueError('Exact complete fixed45/1350 scope')
 field_keys=[(f['section'],f['field'])for f in fields];cells=[]
 for a,agent in enumerate(raw):
  actual=[(section,field)for section,values in agent.items()if section!='agent_name'for field in values]
  if actual!=field_keys:raise ValueError(('Exact whole original field roster/order',a))
  for f,item in enumerate(fields):
   row=frozen[a*45+f];text=agent[item['section']][item['field']]
   if (row['agent_ordinal1'],row['agent_name'],row['section'],row['field'],row['raw_value'])!=(a+1,agent['agent_name'],item['section'],item['field'],text):raise ValueError('Raw field/identity/order loss')
   if hashlib.sha256(text.encode('utf-8')).hexdigest()!=row['source_raw_UTF8_SHA256']:raise ValueError('Exact frozen cell hash')
   tag,flag=none_found_author_status(text,row)
   cells.append(dict(cell_ordinal1=a*45+f+1,agent_ordinal1=a+1,field_ordinal1=f+1,agent_name=agent['agent_name'],section=item['section'],field=item['field'],source_pointer=row['source_pointer'],raw_value=text,source_raw_UTF8_SHA256=row['source_raw_UTF8_SHA256'],author_status=tag,none_found=flag,whole_cell_only_sensitivity=text.strip().casefold()=='none found',broader_marker_sensitivity=bool(re.search(r'\bnone\s+found\b',text,re.I)),individual_qualification_rationale=row['individual_qualification_rationale'],literal_any_information_semantics_ambiguous=row['literal_any_information_semantics_ambiguous'],known_cross_agent_reference_inconsistency=row['known_cross_agent_reference_inconsistency']))
 if len(cells)!=1350:raise ValueError('No source cell excluded')
 safety_fields=matrix['eight_safety_fields'];safety=[c for c in cells if c['section']=='Safety, evaluation & impact']
 if len(safety)!=240 or [c['field']for c in safety[:8]]!=safety_fields:raise ValueError('All original safety8 fields/all30x8')
 agents=matrix['all30_agent_order'];sections=list(dict.fromkeys(c['section']for c in cells));category_order=['Enterprise','Browser','Chat'];cohorts=[]
 for category in category_order:
  members=[r['agent_name']for r in raw if r['Product overview']['Category']==category]
  selected=[c for c in safety if c['agent_name']in members]
  cohorts.append(dict(key=category,members=members,cell_ordinals1=[c['cell_ordinal1']for c in selected],primary_flags=[c['none_found']for c in selected],literal_whole_cell_flags=[c['whole_cell_only_sensitivity']for c in selected],broader_marker_flags=[c['broader_marker_sensitivity']for c in selected],missing=sum(c['none_found']for c in selected),denominator=len(selected),literal_whole_cell_missing=sum(c['whole_cell_only_sensitivity']for c in selected),broader_marker_missing=sum(c['broader_marker_sensitivity']for c in selected)))
 if [len(c['members'])for c in cohorts]!=[13,5,12]or [c['denominator']for c in cohorts]!=[104,40,96]:raise ValueError('Frozen complete original cohort units')
 def by(items,key,keys):return group_summary([dict(c,group_key=key(c))for c in items],keys)
 complete_cohort_cross_margins=[]
 for category in category_order:
  members=[r['agent_name']for r in raw if r['Product overview']['Category']==category]
  selected=[c for c in cells if c['agent_name']in members]
  safe_selected=[c for c in safety if c['agent_name']in members]
  complete_cohort_cross_margins.append(dict(cohort=category,complete_all45=by(selected,lambda c:category,[category])[0],by_section=by(selected,lambda c:c['section'],sections),by_safety_field=by(safe_selected,lambda c:c['field'],safety_fields)))
 fig3=dict(missing=sum(c['none_found']for c in cells),denominator=1350,complete_30x45_primary_flags=[[c['none_found']for c in cells[a*45:(a+1)*45]]for a in range(30)],per_agent=by(cells,lambda c:c['agent_name'],agents),per_field=by(cells,lambda c:c['field_ordinal1'],list(range(1,46))),per_section=by(cells,lambda c:c['section'],sections),literal_whole_cell_missing=sum(c['whole_cell_only_sensitivity']for c in cells),broader_marker_missing=sum(c['broader_marker_sensitivity']for c in cells))
 fig6=dict(missing=sum(c['none_found']for c in safety),denominator=240,complete_30x8_primary_flags=[[c['none_found']for c in safety[a*8:(a+1)*8]]for a in range(30)],per_agent=by(safety,lambda c:c['agent_name'],agents),per_field=by(safety,lambda c:c['field'],safety_fields),cohorts=cohorts,literal_whole_cell_missing=sum(c['whole_cell_only_sensitivity']for c in safety),broader_marker_missing=sum(c['broader_marker_sensitivity']for c in safety))
 checks=[]
 def exact(name,n,d,tn,td):checks.append(dict(id=name,numerator=n,denominator=d,target_numerator=tn,target_denominator=td,passed=type(n)is int and type(d)is int and n==tn and d==td))
 exact('Fig3_all1350',fig3['missing'],1350,198,1350);exact('Fig6_all240',fig6['missing'],240,133,240)
 for c,n,d,display in zip(cohorts,[67,25,41],[104,40,96],['64','63','43']):
  exact('Fig6_'+c['key'],c['missing'],c['denominator'],n,d)
  q=Fraction(100*c['missing'],c['denominator']);t=Fraction(display);half=Fraction(1,2)
  checks.append(dict(id='Fig6_'+c['key']+'_percentage_display',numerator=c['missing'],denominator=c['denominator'],percentage_exact_fraction=str(q),target_display=display,rounding_interval='[display-0.5,display+0.5) percent',passed=t-half<=q<t+half))
 caption=[]
 for label,n,d,display in [('Browser',67,104,'64'),('Enterprise',25,40,'63'),('Chat',41,96,'43')]:
  actual=next(c for c in cohorts if c['key']==label)
  caption.append(dict(literal_category=label,literal_numerator=n,literal_denominator=d,literal_percentage_display=display,actual_numerator=actual['missing'],actual_denominator=actual['denominator'],literal_exact_fraction_passed=actual['missing']==n and actual['denominator']==d,role='MANDATORY_SUPPORTING_LITERAL_CAPTION_AUDIT_NOT_FULL'))
 statuses=list(dict.fromkeys(c['author_status']for c in cells))
 result=dict(schema='AI_AGENT_INDEX_COMPLETE_TRANSPARENCY_RESULT029',source_mode='PRIMARY_ORIGINAL_JSON',original_input_ref=cfg['original_JSON_ref'],original_JSON_ref=cfg['original_JSON_ref'],original_CSV_ref=cfg['original_CSV_ref'],all1350_source_evidence_map_ref=cfg['all1350_source_evidence_map_ref'],matrix_contract_ref=cfg['matrix_contract_ref'],ROOT258_scope_decision_ref=cfg['ROOT258_scope_decision_ref'],all30_agent_order=agents,all45_ordered_fields=fields,all1350_cells=cells,Fig3=fig3,Fig6=fig6,all_source_status_classes=by(cells,lambda c:c['author_status'],statuses),complete_cohort_cross_margins=complete_cohort_cross_margins,primary_target_comparisons=checks,all_primary_published_targets_passed=all(c['passed']for c in checks),mandatory_literal_caption_audit=caption,all_literal_caption_audits_passed=all(c['literal_exact_fraction_passed']for c in caption),word_mean14=dict(role='HELD_AUXILIARY',published_text='14 words',computed=False,reason='Unreleased original tokenizer/markup/nonempty denominator generator'),all_other_original_fields_retained=True,all_other_paper_claims_reproduced=False,FULL_reproduction_qualified=False,paper_credit=0)
 root=Path(cfg['scientific_output_root']);root.mkdir(parents=False,exist_ok=False)
 result_ref=save(root/'PRIMARY_COMPLETE_ORIGINAL_JSON_TRANSPARENCY029.json',result)
 return dict(result_ref=result_ref,all_primary_published_targets_passed=result['all_primary_published_targets_passed'],paper_credit=0)
