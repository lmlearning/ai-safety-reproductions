"""Dormant structural projection only. Unknown text and every numeric value stay opaque.

This projection does NOT qualify the original 1000 IDs, model identities, raw-to-CSV
joins, or three-expert aggregation. Those are an exterior, unresolved map contract.
No data is read on import; no network, native, subprocess, or dynamic code API.
"""
import csv
import hashlib
import io
import pathlib
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

MODELS = ('claude', 'ds_llama', 'ds_qwen', 'gemini', 'gpt4o', 'gpt4omini',
          'llama_3', 'qwen_2', 'qwen_3', 'human')
KNOWN_LABELS = frozenset(
    ('Guidance', 'Informativeness', 'Relevance', 'Safety', 'Empathy', 'Helpfulness', 'Understanding')
    + ('context', 'response', 'Claude-3.5-Haiku', 'deepseek-llama', 'deepseek-qwen', 'Gemini',
       'gpt-4o', 'gpt-4omini', 'Llama-3.1', 'Qwen-2.5', 'Qwen-3', 'judge_response_original')
    + tuple(f'{role}_response_{m}' for role in ('human', 'judge') for m in MODELS))


def text_metadata(s):
    b = s.encode('utf-8')
    normalized = ' '.join(unicodedata.normalize('NFKC', s).split()).encode('utf-8')
    q = {'utf8_sha256': hashlib.sha256(b).hexdigest(), 'codepoints': len(s), 'bytes': len(b),
         'diagnostic_NFKC_whitespace_sha256': hashlib.sha256(normalized).hexdigest(),
         'normalized_hash_never_substitutes_original_identity': True}
    # Exact source-fixed literal match only. No numeric/text/substring heuristics.
    q['recognized_source_literal'] = s if s in KNOWN_LABELS else None
    q['unknown_text_suppressed'] = s not in KNOWN_LABELS
    return q


def csv_projection(path, guard):
    csv.field_size_limit(262144)
    h = hashlib.sha256()
    rows, widths, id_rows = 0, {}, []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)  # Explicit original pandas CSV default, not a schema inference.
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError('Empty source CSV')
        if len(header) > 2000:
            raise ValueError('CSV structural column cap')
        headers = [{'ordinal': i + 1, **text_metadata(s)} for i, s in enumerate(header)]
        id_columns = [(i, s) for i, s in enumerate(header) if s in ('context', 'response')]
        for r in reader:
            rows += 1
            if rows % 25 == 0:
                guard()
            if rows > 100000 or len(r) > 2000:
                raise ValueError('CSV structural object cap')
            widths[str(len(r))] = widths.get(str(len(r)), 0) + 1
            id_rows.append({'CSV_data_row_ordinal_1based': rows,
                            'source_named_candidate_fields': [
                                {'source_header': name, **text_metadata(r[i])}
                                for i, name in id_columns if i < len(r)]})
            # Complete ordered content digest, no raw responses/ratings/ID scalars emitted.
            for s in r:
                b = s.encode('utf-8')
                h.update(len(b).to_bytes(8, 'little'))
                h.update(b)
    for record in id_rows:
        for field in record['source_named_candidate_fields']:
            field['recognized_source_literal'] = None
            field['unknown_text_suppressed'] = True
    multiplicity = {}
    for record in id_rows:
        for field in record['source_named_candidate_fields']:
            key = field['source_header'] + '/' + field['utf8_sha256']
            multiplicity.setdefault(key, []).append(record['CSV_data_row_ordinal_1based'])
    return {'kind': 'CSV', 'header': headers, 'data_rows': rows, 'width_counts': widths,
            'all_row_candidate_ID_witnesses': id_rows,
            'candidate_ID_witnesses_do_not_assert_unique_1000_cohort': True,
            'candidate_field_multiplicities': [{'source_header_and_hash': k, 'count': len(v), 'source_row_ordinals': v}
                                               for k, v in sorted(multiplicity.items())],
            'ordered_decoded_cell_digest': h.hexdigest(), 'dialect_qualification': 'NOT_INFERRED',
            'original_scientific_schema_qualified': False}


class XMLStream:
    def __init__(self, raw, guard, budget):
        self.raw, self.guard, self.budget, self.tail = raw, guard, budget, b''

    def read(self, n=-1):
        self.guard()
        if n < 0 or n > 65536:
            n = 65536
        b = self.raw.read(n)
        self.budget[0] += len(b)
        if self.budget[0] > 256 * 1024 * 1024:
            raise ValueError('Uncompressed XML input cap')
        if b'\x00' in b:
            raise ValueError('Non-UTF8 XML encoding needs separate structural qualification')
        s = (self.tail + b).upper()
        if b'<!DOCTYPE' in s or b'<!ENTITY' in s:
            raise ValueError('DTD/entity forbidden')
        self.tail = s[-16:]
        return b


def _events(z, name, guard, budget):
    with z.open(name) as raw:
        yield from ET.iterparse(XMLStream(raw, guard, budget), events=('end',))


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def xlsx_projection(path, guard):
    budget = [0]
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if len(infos) > 2000 or len(names) != len(set(names)):
            raise ValueError('ZIP duplicate/member cap')
        for i in infos:
            p = pathlib.PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in i.filename or i.flag_bits & 1:
                raise ValueError('Unsafe/encrypted ZIP member')
            if i.file_size > 128 * 1024 * 1024:
                raise ValueError('ZIP member byte cap')
        if sum(i.file_size for i in infos) > 256 * 1024 * 1024:
            raise ValueError('ZIP expansion cap')
        if 'xl/workbook.xml' not in names:
            raise ValueError('Not an XLSX workbook')
        # Preserve opaque sheet identifiers; no arbitrary structural text exception adopted.
        sheets = []
        for _, e in _events(z, 'xl/workbook.xml', guard, budget):
            if _local(e.tag) == 'sheet':
                sheets.append({'sheet_name': text_metadata(e.attrib.get('name', '')),
                               'sheet_id': text_metadata(e.attrib.get('sheetId', '')),
                               'relationship_id': text_metadata(next((v for k, v in e.attrib.items() if _local(k) == 'id'), ''))})
                e.clear()
        # Retain shared-string hashes/known labels only, never shared-string bodies.
        shared = []
        if 'xl/sharedStrings.xml' in names:
            for _, e in _events(z, 'xl/sharedStrings.xml', guard, budget):
                if _local(e.tag) == 'si':
                    s = ''.join(t.text or '' for t in e.iter() if _local(t.tag) == 't')
                    shared.append(text_metadata(s))
                    if len(shared) > 500000:
                        raise ValueError('Shared-string object cap')
                    e.clear()
        projections = []
        for name in sorted(n for n in names if re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml', n)):
            guard()
            cells, rows, row1, digest = 0, 0, [], hashlib.sha256()
            identity_columns, identity_cells = {}, []
            for _, e in _events(z, name, guard, budget):
                tag = _local(e.tag)
                if tag == 'c':
                    cells += 1
                    if cells > 1000000:
                        raise ValueError('Worksheet cell cap')
                    coordinate = e.attrib.get('r', '')
                    if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}', coordinate):
                        raise ValueError('Unknown cell coordinate')
                    typ = e.attrib.get('t', 'n')
                    raw = ''.join(t.text or '' for t in e.iter() if _local(t.tag) in ('v', 't', 'f'))
                    # Hash formulas/caches too; never report their content or numeric value.
                    meta = text_metadata(raw)
                    if typ == 's':
                        v = next((t.text for t in e if _local(t.tag) == 'v'), None)
                        if v is None or not v.isdecimal() or int(v) >= len(shared):
                            raise ValueError('Shared-string index invalid')
                        meta = shared[int(v)]
                    elif typ not in ('inlineStr', 'str'):
                        meta = {**meta, 'recognized_source_literal': None, 'unknown_text_suppressed': True}
                    digest.update(coordinate.encode('ascii') + b'\0' + typ.encode('ascii') + bytes.fromhex(meta['utf8_sha256']))
                    if re.fullmatch(r'[A-Z]{1,3}1', coordinate):
                        if len(row1) >= 2000:
                            raise ValueError('Header object cap')
                        row1.append({'cell': coordinate, 'type': typ, **meta})
                        if meta['recognized_source_literal'] in ('context', 'response'):
                            identity_columns[re.match(r'[A-Z]+', coordinate).group()] = meta['recognized_source_literal']
                    else:
                        col = re.match(r'[A-Z]+', coordinate).group()
                        if col in identity_columns:
                            if len(identity_cells) >= 100000:
                                raise ValueError('Candidate identity cell cap')
                            identity_cells.append({'cell': coordinate, 'source_header': identity_columns[col],
                                **meta, 'recognized_source_literal': None, 'unknown_text_suppressed': True})
                    e.clear()
                elif tag == 'row':
                    rows += 1
                    e.clear()
            projections.append({'member': name, 'rows': rows, 'cells': cells,
                                'row1_only_not_assumed_scientific_header': row1,
                                'candidate_context_response_identity_cells': identity_cells,
                                'candidate_identity_requires_positive_source_and_crossfile_qualification': True,
                                'ordered_cell_metadata_digest': digest.hexdigest()})
        return {'kind': 'XLSX', 'sheet_identifiers_opaque': sheets,
                'worksheets': projections, 'uncompressed_xml_bytes': budget[0],
                'sheet_relationship_binding_qualified': False,
                'original_scientific_schema_qualified': False}


def inspect(path, guard):
    suffix = pathlib.Path(path).suffix.lower()
    if suffix == '.csv':
        return csv_projection(path, guard)
    if suffix == '.xlsx':
        return xlsx_projection(path, guard)
    raise ValueError('Only exact manifest CSV/XLSX inputs allowed')
