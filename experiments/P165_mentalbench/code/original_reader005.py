"""Independent original CSV/human-workbook reader; dormant source only."""
import csv,hashlib,json,math,struct,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MODELS=('claude','ds_llama','ds_qwen','gemini','gpt4o','gpt4omini','llama_3','qwen_2','qwen_3','human')
JUDGES=('Claude','GPT-4o','Gemini','o4-mini')
ATTRS=('Guidance','Informativeness','Relevance','Safety','Empathy','Helpfulness','Understanding')
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REASONS=('VALID','PANDAS_NA_OR_EMPTY','JSON_ERROR','ATTRIBUTE_ABSENT','NONE_OR_EMPTY_ATTRIBUTE','FLOAT_ERROR','NAN_VALUE','NONFINITE_UNSUPPORTED','VALID_SOURCE_OUT_OF_RUBRIC_RETAINED')
def need(x,m):
    if not x:raise ValueError(m)
def pin(p):
    p=Path(p).resolve();h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def verify(q):
    need(type(q)is dict and all(k in q for k in ('path','bytes','sha256')),'complete original pin')
    need(pin(q['path'])=={k:q[k]for k in ('path','bytes','sha256')},'original pin changed '+q['path'])
    if 'Git_blob_SHA1'in q:
        h=hashlib.sha1();h.update(('blob '+str(q['bytes'])+'\0').encode('ascii'))
        with Path(q['path']).open('rb')as f:
            while b:=f.read(1048576):h.update(b)
        need(h.hexdigest()==q['Git_blob_SHA1'],'independent original Git blob mismatch')
def digest(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def identity(row,spec):
    if spec['kind']=='exact_column_utf8_sha256':return digest(row[spec['column']])
    need(spec['kind']=='exact_composite_utf8_fields_length_prefixed_sha256','ID kind')
    prefix=spec['length_prefix'];need(prefix=='uint64_little_endian','source-exact qualified ID framing')
    h=hashlib.sha256()
    for name in spec['columns']:
        b=row[name].encode('utf-8');h.update(struct.pack('<Q',len(b)));h.update(b)
    return h.hexdigest()
def parse_attributes(raw,NA):
    if raw is None or raw in NA or raw=='':return [None]*7,[1]*7
    text=str(raw).strip()
    if text.startswith('```json'):text=text.replace('```json','').replace('```','').strip()
    try:d=json.loads(text)
    except Exception:return [None]*7,[2]*7
    if not isinstance(d,dict):return [None]*7,[2]*7
    values=[];reasons=[]
    for a in ATTRS:
        if a not in d:values.append(None);reasons.append(3);continue
        v=d[a]
        if v is None or v=='':values.append(None);reasons.append(4);continue
        try:v=float(v)
        except (TypeError,ValueError,OverflowError):values.append(None);reasons.append(5);continue
        if math.isnan(v):values.append(None);reasons.append(6)
        elif not math.isfinite(v):raise ValueError('source float produced infinity; not silently dropped or clipped')
        else:values.append(v);reasons.append(0 if 1<=v<=5 else 8)
    return values,reasons
def workbook_json_cells(spec):
    verify(spec['input_ref']);wanted={}
    for c in spec['score_cells']:
        key=(c['worksheet_member'],c['cell']);need(key not in wanted,'duplicate physical human cell');wanted[key]=c
    need(len(wanted)==10000,'all1000x10 raw-human JSON cells')
    values={};origins=[];observed=set()
    with zipfile.ZipFile(spec['input_ref']['path']) as z:
        members={x.filename:x for x in z.infolist()};need(len(members)==len(z.infolist()),'duplicate ZIP member')
        shared=[];sm=spec.get('shared_strings_member')
        if sm:
            need(members[sm].file_size<=67108864,'bounded shared strings')
            with z.open(sm) as f:
                for event,node in ET.iterparse(f,events=('end',)):
                    if node.tag==NS+'si':shared.append(''.join(t.text or '' for t in node.iter(NS+'t')));node.clear()
        for member in sorted({m for m,c in wanted}):
            need(members[member].file_size<=67108864,'bounded human sheet')
            with z.open(member) as f:
                for event,node in ET.iterparse(f,events=('end',)):
                    if node.tag!=NS+'c':continue
                    key=(member,node.attrib.get('r'))
                    if key in wanted:
                        c=wanted[key];need(key not in observed,'duplicate mapped XML cell');observed.add(key);formula=node.find(NS+'f');typ=node.attrib.get('t');v=node.find(NS+'v')
                        cache_present=v is not None and v.text is not None
                        raw='' if typ=='e' else shared[int(v.text)] if typ=='s' and cache_present else ''.join(t.text or '' for t in node.iter(NS+'t')) if typ=='inlineStr' and formula is None else (v.text if cache_present else '')
                        need(c['record_id'] and c['model'] in MODELS,'qualified human cell IDs');target=(c['record_id'],c['model']);need(target not in values,'duplicate semantic human slot');values[target]=raw
                        origins.append(dict(record_id=c['record_id'],model=c['model'],worksheet_member=member,cell=key[1],raw_utf8_sha256=digest(raw),physical_cell_present=True,formula_present=formula is not None,cached_v_present=cache_present,excel_error=typ=='e',data_only_reason='excel_error_missing' if typ=='e' else 'formula_cached_value' if formula is not None and cache_present else 'formula_without_cached_value_missing' if formula is not None else 'literal_or_empty_cell'))
                    node.clear()
    for key,c in wanted.items():
        if key not in observed:
            target=(c['record_id'],c['model']);need(target not in values,'duplicate absent semantic slot');values[target]='';origins.append(dict(record_id=c['record_id'],model=c['model'],worksheet_member=key[0],cell=key[1],raw_utf8_sha256=digest(''),physical_cell_present=False,formula_present=False,cached_v_present=False,excel_error=False,data_only_reason='absent_XML_cell_missing'))
    need(len(values)==10000,'all mapped semantic slots including absent XML');verify(spec['input_ref']);return values,origins
def read_originals(mapping,hash_file,reason_file):
    need(mapping['schema']=='ROOT_QUALIFIED_COMPLETE_MENTALBENCH_ORIGINAL_MAP001','qualified original map schema')
    for k in ('ROOT_exact_original_headers_and_IDs_qualified','ROOT_all5_raw_workbooks_to_all4_paperdate_CSVs_qualified','ROOT_complete_1000x10x7x4_original_slots_qualified','ROOT_released_human_reference_aggregation_provenance_qualified','ROOT_original_missingness_and_source_parser_policy_qualified'):need(mapping[k] is True,k)
    need(mapping.get('three_individual_human_raters_present_claimed')is False,'released single human reference only, no fabricated expert arrays')
    refs=mapping['all_original_input_refs'];need(len(refs)==9 and len({q['path'] for q in refs})==9,'exact nine original inputs')
    for q in refs:verify(q)
    ids=mapping['ordered_original_identity_sha256'];need(type(ids)is list and len(ids)==len(set(ids))==1000 and all(type(x)is str and len(x)==64 and all(c in '0123456789abcdef' for c in x) for x in ids),'complete ordered list of1000 qualified RECORD SHA256 IDs, not an aggregate roster hash')
    need(set(mapping['judge_csv_maps'])==set(JUDGES),'all four judges')
    hs=mapping['independent_human_reference_map'];need(hs['input_ref'] in refs,'original human workbook pin');human_raw,origins=workbook_json_cells(hs)
    human={m:{a:[] for a in ATTRS} for m in MODELS};human_values={};human_parse=[];CSV_human_reference={};raw_human_CSV_discrepancies=[]
    for rid in ids:
        for m in MODELS:
            vals,why=parse_attributes(human_raw[(rid,m)],hs['exact_source_pandas_NA_lexemes']);human_values[(rid,m)]=vals
            human_parse.append(dict(record_id=rid,model=m,reasons=why))
    pairs={j:{a:{m:[] for m in MODELS} for a in ATTRS} for j in JUDGES};lineage=[];reason_counts={x:0 for x in REASONS};csv.field_size_limit(16777216)
    with Path(hash_file).open('xb') as hashes,Path(reason_file).open('xb') as reasons:
        for j in JUDGES:
            spec=mapping['judge_csv_maps'][j];need(spec['input_ref'] in refs,'CSV original pin');seen={}
            with Path(spec['input_ref']['path']).open('r',encoding=spec['encoding'],newline='') as f:
                reader=csv.reader(f,delimiter=spec['delimiter'],quotechar=spec['quotechar']);head=next(reader);need(head==spec['exact_header'] and len(head)==len(set(head)),'exact original header');previous=reader.line_num
                for ordinal,fields in enumerate(reader,1):
                    need(len(fields)==len(head),'CSV row width');row=dict(zip(head,fields));rid=identity(row,spec['identity_key']);need(rid not in seen,'duplicate original record ID');seen[rid]={}
                    lineage.append(dict(judge=j,data_row_ordinal=ordinal,physical_start_line=previous+1,physical_end_line=reader.line_num,record_id=rid));previous=reader.line_num
                    for m in MODELS:
                        columns=[f'human_response_{m}',f'judge_response_{m}'];need(all(c in row for c in columns),'required exact paper-era response columns')
                        parsed=[]
                        for col in columns:
                            raw=row[col];hashes.write(hashlib.sha256(raw.encode()).digest());vals,why=parse_attributes(raw,spec['exact_source_pandas_NA_lexemes']);parsed.append(vals);reasons.write(bytes(why))
                            for code in why:reason_counts[REASONS[code]]+=1
                        need((rid,m) in human_values,'CSV ID in raw human roster')
                        # Original paper-date CSV reference/missingness is the analysis input.
                        # Raw workbook differences are provenance, never replacement values.
                        if j==JUDGES[0]:CSV_human_reference[(rid,m)]=parsed[0]
                        else:need(parsed[0]==CSV_human_reference[(rid,m)],'four original CSV human references/missing masks differ')
                        if parsed[0]!=human_values[(rid,m)]:
                            raw_human_CSV_discrepancies.append(dict(judge=j,record_id=rid,model=m,raw_workbook_values=human_values[(rid,m)],original_CSV_values=parsed[0],raw_defined_mask=[v is not None for v in human_values[(rid,m)]],CSV_defined_mask=[v is not None for v in parsed[0]],source_CSV_not_filled=True))
                        seen[rid][m]=parsed
            need(len(seen)==1000 and set(seen)==set(ids),'full original CSV cohort')
            for rid in ids:
                for m in MODELS:
                    h,l=seen[rid][m]
                    for a,x,y in zip(ATTRS,h,l):pairs[j][a][m].append((x,y))
            verify(spec['input_ref'])
    need(len(CSV_human_reference)==10000,'all1000x10 canonical released CSV references')
    for rid in ids:
        for m in MODELS:
            for a,v in zip(ATTRS,CSV_human_reference[(rid,m)]):human[m][a].append(v)
    need(len(lineage)==4000,'all four original row lineages')
    for q in refs:verify(q)
    return human,pairs,ids,dict(human_analysis_input='ORIGINAL_PAPERDATE_FOUR_CSV_HUMAN_COLUMNS',all_four_CSV_human_values_and_missing_masks_agree=True,raw_human_CSV_discrepancies=raw_human_CSV_discrepancies,raw_workbook_values_used_to_fill_CSV=False,three_expert_arrays_or_historical_aggregation_producer_verified=False,row_lineage=lineage,raw_human_cell_origins=origins,raw_human_parse_reasons=human_parse,CSV_parse_reason_counts=reason_counts,CSV_hash_order='judge order; CSV source record order; model order; H then L;32byteSHA256 percell',CSV_reason_order='same cell order;7attribute reason bytes percell',reason_code_roster=list(REASONS),all_input_refs=refs)
