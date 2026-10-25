import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_vocabulary_is_unique_and_typed():
 d=json.loads((ROOT/'knowledge/evidence_vocabulary.json').read_text(encoding='utf-8')); names=[x['name'] for x in d['terms']]
 assert len(names)==len(set(names)); assert len(names)>=80
 assert all(x['type'] in {'boolean','enum','number','string'} for x in d['terms'])
def test_all_case_evidence_terms_are_declared():
 v=json.loads((ROOT/'knowledge/evidence_vocabulary.json').read_text(encoding='utf-8')); known={x['name'] for x in v['terms']}
 c=json.loads((ROOT/'knowledge/case_library.json').read_text(encoding='utf-8'))
 assert all(set(x['evidence_terms'])<=known for x in c['cases'])
