"""Complete original data integrity and source-order preparation; inert functions."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

TOKEN=re.compile(r'<[^>]+>')
ENTITY={f'<e_{i}>'for i in range(200)}
RELATION={f'<r_{i}>'for i in range(10)}
EXPECTED_VOCAB=[f'<e_{i}>'for i in range(200)]+[f'<r_{i}>'for i in range(10)]+['<mask>','<sep>','<a>','</a>','<q>','</q>']
HELD_TYPES=[f'{i}hop_test'for i in range(2,41)]

def require(ok,message):
    if not ok:raise RuntimeError(message)

def fields(row):
    require(set(row)=={'input_text','target_text','type'},'Original three complete row fields required')
    text=row['input_text'];target=row['target_text'];tp=row['type']
    require(all(type(x)is str for x in (text,target,tp)),'Literal original row strings required')
    tokens=TOKEN.findall(text);out=TOKEN.findall(target)
    require(''.join(tokens)==text and ''.join(out)==target,'Unknown characters outside original token grammar')
    require(len(tokens)>=2 and tokens[0]in ENTITY and all(x in RELATION for x in tokens[1:]),'Original entity/relation chain')
    require(out[:-2]==tokens and out[-2]in ENTITY and out[-1]=='</a>','Exact original target prefix/tail/end marker')
    return tokens,out[-2],tp

def validate_original(train_path,test_path,vocab_path,guard):
    """All released rows retained; only author all_splits selects neural test inputs."""
    guard.check('before complete original JSON parsing',force=True)
    vocab_list=json.loads(Path(vocab_path).read_bytes())
    require(vocab_list==EXPECTED_VOCAB,'Full original216-token vocabulary and order')
    vocab={x:i for i,x in enumerate(['<pad>']+vocab_list)}
    train=json.loads(Path(train_path).read_bytes());test=json.loads(Path(test_path).read_bytes())
    require(type(train)is list and type(test)is list,'Whole released JSON lists')
    # Full graph is independently recovered from every actual atomic row, not regenerated.
    graph={};atomic_seen=0;types_train=Counter();types_test=Counter()
    for rows,label in ((train,'train'),(test,'test')):
        for i,row in enumerate(rows):
            tokens,tail,tp=fields(row)
            if len(tokens)==2:
                require(tp in ('atomic','atomic_facts'),'Unexpected atomic type')
                key=tuple(tokens);prior=graph.setdefault(key,tail);require(prior==tail,'Conflicting original atomic graph')
                atomic_seen+=1
            (types_train if label=='train' else types_test)[tp]+=1
            if i%2048==0:guard.check('all original raw rows '+label+' '+str(i))
    require(len(graph)==2000 and set(h for h,r in graph)==ENTITY and set(r for h,r in graph)==RELATION,'All2000 original atomic edges')
    for r in RELATION:require({graph[(h,r)]for h in ENTITY}==ENTITY,'Original relation is complete200-entity permutation')
    train_inputs=set();held=[];held_source=[];held_hops=[];held_targets=[];held_inputs=[];held_lengths=[]
    chain_count=0;type_geometry=Counter()
    for rows,label in ((train,'train'),(test,'test')):
        for i,row in enumerate(rows):
            tokens,tail,tp=fields(row);h=tokens[0];hop=len(tokens)-1
            for relation in tokens[1:]:h=graph[(h,relation)]
            require(h==tail,'Every original raw graph chain/target must agree')
            chain_count+=1;type_geometry[(label,tp,hop)]+=1
            if label=='train':
                require(tp==('atomic'if hop==1 else str(hop-2)+'hop_train'),'Exact source combine_facts training label convention')
                require(row['input_text']not in train_inputs,'Duplicate original training chain')
                train_inputs.add(row['input_text'])
            elif tp in HELD_TYPES:
                require(tp==str(hop)+'hop_test','Held-out source type/hop geometry')
                require(row['input_text']not in train_inputs,'Held-out training-chain overlap')
                require(len(tokens)<=50,'No author max_len50 input truncation permitted')
                held_source.append(i);held_hops.append(hop);held_targets.append(vocab[tail]);held_lengths.append(len(tokens))
                ids=[vocab[x]for x in tokens];held_inputs.append(ids+[0]*(50-len(ids)));held.append(row)
            if i%2048==0:guard.check('whole graph/training-overlap '+label+' '+str(i))
    require(len(train)==587000,'Complete source training rows2000+39*15000')
    require(len(held)==29250 and Counter(held_hops)==Counter({x:750 for x in range(2,41)}),'Every39 held-out hops/all750 examples')
    require(len({x['input_text']for x in held})==29250,'Complete held-out input uniqueness')
    # Never infer sizes/counts of extra test types from the large public file listing.
    extras={k:v for k,v in types_test.items()if k not in HELD_TYPES}
    result={'raw_train_rows':len(train),'raw_test_rows':len(test),'all_train_type_counts':dict(types_train),'all_test_type_counts':dict(types_test),'all_extra_test_types_retained_excluded_only_by_original_all_splits':extras,'all_raw_graph_chains_verified':chain_count,'atomic_rows_observed':atomic_seen,'unique_atomic_edges':2000,'all_39_hops':list(range(2,41)),'heldout_per_hop':750,'heldout_rows':29250,'vocab_size_with_source_pad':217,'input_shape':[29250,50],'train_label_source_offset_preserved':True,'graph_SHA256':hashlib.sha256(json.dumps(sorted((h,r,t)for(h,r),t in graph.items()),separators=(',',':')).encode()).hexdigest()}
    guard.check('after full original data integrity',force=True)
    del train,test,train_inputs,held
    return {'inputs':held_inputs,'targets':held_targets,'source_indices':held_source,'hops':held_hops,'lengths':held_lengths,'vocab':vocab,'integrity':result}

def write_prepared(np,data,out,guard):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);refs={}
    for name,dtype in (('inputs','<u2'),('targets','<u2'),('source_indices','<u4'),('hops','u1'),('lengths','u1')):
        a=np.asarray(data[name],dtype=dtype);p=out/(name+'.bin')
        with p.open('xb')as f:require(f.write(memoryview(a).cast('B'))==a.nbytes,'Complete prepared array write')
        h=hashlib.sha256()
        with p.open('rb')as f:
            for b in iter(lambda:f.read(1024**2),b''):h.update(b)
        refs[name]={'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest(),'shape':list(a.shape),'dtype':dtype}
        guard.check('complete prepared '+name)
    return refs
