import json
from pathlib import Path
import pytest
from src.knowledge.source_audit import KnowledgeAuditError, audit_knowledge_base
ROOT=Path(__file__).resolve().parents[1]
ARGS=dict(registry_path=ROOT/'knowledge/source_registry.json',case_library_path=ROOT/'knowledge/case_library.json',rules_path=ROOT/'knowledge/diagnostic_rules.json',vocabulary_path=ROOT/'knowledge/evidence_vocabulary.json',scenario_matrix_path=ROOT/'knowledge/scenario_matrix.json')
def test_real_knowledge_base_audit():
 s=audit_knowledge_base(**ARGS); assert s.source_count==40; assert s.case_count==90; assert s.rule_count==90; assert s.scenario_count==720; assert 'NIST_SP800_82_R4_IPD_2026' in s.draft_source_ids
@pytest.mark.parametrize('name',list(ARGS))
def test_missing_file(name,tmp_path):
 args=dict(ARGS); args[name]=tmp_path/'missing.json'
 with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**args)
def mutate(tmp_path,key,mutator):
 args={};
 for name,p in ARGS.items():
  d=json.loads(Path(p).read_text(encoding='utf-8')); mutator(d) if name==key else None
  q=tmp_path/f'{name}.json'; q.write_text(json.dumps(d),encoding='utf-8'); args[name]=q
 return args
@pytest.mark.parametrize('key,mutator',[
('registry_path',lambda d:d.update(sources=[])),
('registry_path',lambda d:d['sources'].append('bad')),
('registry_path',lambda d:d['sources'].append(dict(d['sources'][0]))),
('registry_path',lambda d:d['sources'][0].update(url='http://bad.example')),
('registry_path',lambda d:d.update(aliases=[])),
('registry_path',lambda d:d['aliases'].update({'OLD':'NOPE'})),
('case_library_path',lambda d:d.update(cases=[])),
('case_library_path',lambda d:d['cases'].append('bad')),
('case_library_path',lambda d:d['cases'][1].update(case_id=d['cases'][0]['case_id'])),
('case_library_path',lambda d:d['cases'][0].update(source_ids=['NOPE'])),
('case_library_path',lambda d:d['cases'][0].update(physical_action_authorized=True)),
('case_library_path',lambda d:d['cases'][0].update(rule_status='bad')),
('rules_path',lambda d:d.update(rules=[])),
('rules_path',lambda d:d['rules'].append('bad')),
('rules_path',lambda d:d['rules'][1].update(rule_id=d['rules'][0]['rule_id'])),
('rules_path',lambda d:d['rules'][0].update(case_id='NOPE')),
('rules_path',lambda d:d['rules'][1].update(case_id=d['rules'][0]['case_id'])),
('vocabulary_path',lambda d:d.update(terms=[])),
('vocabulary_path',lambda d:d['terms'].append('bad')),
('vocabulary_path',lambda d:d['terms'][1].update(name=d['terms'][0]['name'])),
('case_library_path',lambda d:d['cases'][0].update(evidence_terms=['NOPE'])),
('rules_path',lambda d:d['rules'][0]['required_all'][0].update(field='NOPE')),
('scenario_matrix_path',lambda d:d.update(scenarios=[])),
('scenario_matrix_path',lambda d:d.update(scenario_count=d['scenario_count']+1)),
('scenario_matrix_path',lambda d:d['scenarios'][0].update(synthetic=False)),
('scenario_matrix_path',lambda d:d['scenarios'][0].update(case_id='NOPE')),
])
def test_invalid_mutations(tmp_path,key,mutator):
 with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,key,mutator))

def test_invalid_json_syntax_and_root(tmp_path):
    bad = tmp_path/'bad.json'; bad.write_text('{bad', encoding='utf-8')
    args=dict(ARGS); args['registry_path']=bad
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**args)
    bad.write_text('[]', encoding='utf-8')
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**args)

def test_empty_source_id(tmp_path):
    def f(d): d['sources'][0]['id']=''
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,'registry_path',f))

def test_case_without_sources(tmp_path):
    def f(d): d['cases'][0]['source_ids']=[]
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,'case_library_path',f))

def test_case_without_rule(tmp_path):
    def f(d): d['rules'].pop()
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,'rules_path',f))

@pytest.mark.parametrize('key,field,value',[
    ('registry_path','sources',{}),
    ('case_library_path','cases',{}),
    ('rules_path','rules',{}),
    ('vocabulary_path','terms',{}),
    ('scenario_matrix_path','scenarios',{}),
])
def test_wrong_container_types(tmp_path,key,field,value):
    def f(d): d[field]=value
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,key,f))

def test_empty_alias_key(tmp_path):
    def f(d): d['aliases']['']='DUPONT_RO_MANUAL_R19_2026'
    with pytest.raises(KnowledgeAuditError): audit_knowledge_base(**mutate(tmp_path,'registry_path',f))
