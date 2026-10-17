"""Independent Expat OOXML transport; no workbook is read at source import."""
from decimal import Decimal,InvalidOperation
from pathlib import Path,PurePosixPath
import hashlib,math,posixpath,re,xml.parsers.expat,zipfile

RATERS=('AI','Human-Z','Human-S')
COLUMNS={'AI':('D','E','F','G','H','I','J','K','L'),'Human-Z':('N','O','P','Q','R','S','T','U','V'),'Human-S':('X','Y','Z','AA','AB','AC','AD','AE','AF')}
TOTALS={'AI':'M','Human-Z':'W','Human-S':'AG'}

def xml_tree(raw):
    if b'<!DOCTYPE'in raw.upper()or b'<!ENTITY'in raw.upper():raise ValueError('No document type/entity definitions')
    stack=[];root=[];p=xml.parsers.expat.ParserCreate(namespace_separator='}')
    def start(name,attrs):
        node=dict(tag=name.split('}')[-1],attrs={k.split('}')[-1]:v for k,v in attrs.items()},text='',children=[])
        if stack:stack[-1]['children'].append(node)
        else:root.append(node)
        stack.append(node)
    def chars(text):
        if stack:stack[-1]['text']+=text
    p.StartElementHandler=start;p.EndElementHandler=lambda name:stack.pop();p.CharacterDataHandler=chars
    p.ExternalEntityRefHandler=lambda *args:0;p.SetParamEntityParsing(xml.parsers.expat.XML_PARAM_ENTITY_PARSING_NEVER)
    p.Parse(raw,True)
    if len(root)!=1:raise ValueError('One XML document root required')
    return root[0]

def descendants(node,tag):
    for child in node['children']:
        if child['tag']==tag:yield child
        yield from descendants(child,tag)

def text_runs(node):
    if node['tag']=='rPh':return ''
    return(node['text']if node['tag']=='t'else'')+''.join(text_runs(c)for c in node['children'])

def colnum(text):
    n=0
    for c in text:n=n*26+ord(c)-64
    return n

def coltext(n):
    out=''
    while n:n,r=divmod(n-1,26);out=chr(65+r)+out
    return out

def coordinate(text):
    m=re.fullmatch(r'([A-Z]+)([1-9][0-9]*)',text)
    if not m:raise ValueError('Exact ordinary cell coordinate required')
    return colnum(m[1]),int(m[2])

def shifted_formula(formula,master,target):
    mc,mr=coordinate(master);tc,tr=coordinate(target)
    def move(m):
        c=colnum(m[2])if m[1]else colnum(m[2])+tc-mc;r=int(m[4])if m[3]else int(m[4])+tr-mr
        if c<1 or r<1:raise ValueError('Shared formula shifted outside worksheet')
        return m[1]+coltext(c)+m[3]+str(r)
    return re.sub(r'(\$?)([A-Z]+)(\$?)([1-9][0-9]*)',move,formula)

def numeric(cell):
    if cell is None or cell['literal']is None:return None
    if cell['XML_type']not in('n',''):raise ValueError('Non-numeric score/cache cell')
    value=float(cell['literal'])
    if not math.isfinite(value):raise ValueError('Nonfinite input score/cache')
    return value

def formula_sum(expanded,row,rater,cells):
    text=expanded[1:]if expanded.startswith('=')else expanded;text=text.replace(' ','')
    expected=[c+str(row)for c in COLUMNS[rater]]
    m=re.fullmatch(r'SUM\((\$?[A-Z]+\$?[0-9]+):(\$?[A-Z]+\$?[0-9]+)\)',text,re.IGNORECASE)
    if m:
        a,b=(s.replace('$','')for s in m.groups())
        if(a,b)!=(expected[0],expected[-1]):raise ValueError('SUM is not the declared same-row nine criteria')
        total=Decimal(0)
        for ref in expected:
            c=cells.get(ref)
            if c and c['literal']is not None and c['XML_type']in('n',''):total+=Decimal(c['literal'])
        return total
    refs=text.split('+')
    if[ref.replace('$','')for ref in refs]!=expected:raise ValueError('Only exact declared same-row SUM or plus-chain allowed')
    total=Decimal(0)
    for ref in expected:
        c=cells.get(ref)
        if c is None or c['literal']is None:continue
        if c['XML_type']not in('n',''):raise ValueError('Plus-chain text/error is not numeric blank')
        total+=Decimal(c['literal'])
    return total

def read_complete_workbook(ref,guard):
    raw=Path(ref['path']).read_bytes()
    if len(raw)!=ref['bytes']or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('Original workbook whole pin changed')
    guard();cells={};members=[]
    with zipfile.ZipFile(Path(ref['path']))as z:
        infos=z.infolist()
        if sum(i.file_size for i in infos)>10*1024**2 or len(infos)>100:raise ValueError('Finite original workbook ZIP bound')
        for i in infos:
            if i.filename.startswith('/')or'..'in PurePosixPath(i.filename).parts:raise ValueError('Workbook ZIP member containment')
            members.append(dict(name=i.filename,bytes=i.file_size,CRC=i.CRC))
        strings=[]
        if'xl/sharedStrings.xml'in z.namelist():
            strings=[text_runs(n)for n in descendants(xml_tree(z.read('xl/sharedStrings.xml')),'si')]
        book=xml_tree(z.read('xl/workbook.xml'));rels=xml_tree(z.read('xl/_rels/workbook.xml.rels'))
        sheets=[n for n in descendants(book,'sheet')if n['attrs'].get('name')=='Sheet1']
        if len(sheets)!=1:raise ValueError('Exact original Sheet1 required')
        rid=sheets[0]['attrs']['id'];matches=[n for n in descendants(rels,'Relationship')if n['attrs'].get('Id')==rid]
        if len(matches)!=1 or matches[0]['attrs'].get('TargetMode')=='External':raise ValueError('One internal worksheet relationship required')
        target=matches[0]['attrs']['Target'];member=posixpath.normpath(target.lstrip('/')if target.startswith('/')else'xl/'+target)
        if not member.startswith('xl/')or'..'in PurePosixPath(member).parts:raise ValueError('Worksheet relationship escaped original ZIP')
        sheet=xml_tree(z.read(member))
        for n in descendants(sheet,'c'):
            refcell=n['attrs']['r']
            if refcell in cells:raise ValueError('Duplicate OOXML cell coordinate')
            coordinate(refcell);typ=n['attrs'].get('t','n');vs=[c for c in n['children']if c['tag']=='v'];fs=[c for c in n['children']if c['tag']=='f']
            if len(vs)>1 or len(fs)>1:raise ValueError('Ambiguous cell value/formula')
            literal=vs[0]['text']if vs and vs[0]['text']!=''else None
            displayed=strings[int(literal)]if typ=='s'and literal is not None else text_runs(n)if typ=='inlineStr'else literal
            cells[refcell]=dict(XML_type=typ,literal=literal,text_value=displayed,
                formula_text=fs[0]['text']or None if fs else None,formula_attributes=fs[0]['attrs']if fs else{},formula_present=bool(fs))
    masters={}
    for c,v in cells.items():
        if v['formula_attributes'].get('t')=='shared'and v['formula_text']is not None:
            si=v['formula_attributes']['si']
            if si in masters:raise ValueError('Duplicate shared formula master')
            masters[si]=(c,v['formula_text'])
    rows=[]
    for row in range(3,94):
        guard();ids=[]
        for col in('A','B','C'):
            c=cells.get(col+str(row))
            if c is None or c['text_value']is None:raise ValueError('Missing complete case identity')
            ids.append(c['text_value'])
        criteria={r:[numeric(cells.get(c+str(row)))for c in COLUMNS[r]]for r in RATERS}
        totals={};audits={}
        for r in RATERS:
            c=TOTALS[r]+str(row);v=cells.get(c)
            if not v or not v['formula_present']:raise ValueError('Every original total must retain its formula')
            expanded=v['formula_text']
            if expanded is None:
                master,text=masters[v['formula_attributes']['si']];expanded=shifted_formula(text,master,c)
            derived=formula_sum(expanded,row,r,cells);cache=numeric(v)
            if cache is None:raise ValueError('Original cached total missing; no replacement')
            totals[r]=cache;audits[r]=dict(coordinate=c,formula_text=v['formula_text'],formula_attributes=v['formula_attributes'],
                expanded_formula=expanded,cache=cache,derived=float(derived),cache_equal=Decimal(v['literal'])==derived)
        rows.append(dict(row=row,AA=ids[0],AAUni=ids[1],University=ids[2],criteria=criteria,totals=totals,formula_audits=audits))
    return dict(rows=rows),dict(parser='Independent stdlib Expat OOXML; no openpyxl/pandas/primary adapter',workbook_ref=ref,
        exact_ZIP_members=members,shared_string_count=len(strings),all_original_cells=cells,worksheet_member=member,
        original_case_order=list(range(3,94)),numeric_cache_not_repaired=True)
