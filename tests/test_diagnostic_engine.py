from __future__ import annotations
import json, math
from pathlib import Path
import pytest
from src.knowledge.case_library import CaseLibrary, KnowledgeCase
from src.knowledge.diagnostic_engine import DiagnosticRule, DiagnosticRuleError, EvidenceCondition, SourceGroundedDiagnosticEngine, _condition_matches, _rule_matches, load_diagnostic_rules
ROOT=Path(__file__).resolve().parents[1]; RULES=ROOT/'knowledge/diagnostic_rules.json'; LIBRARY=ROOT/'knowledge/case_library.json'; REGISTRY=ROOT/'knowledge/source_registry.json'
def write_json(path,value): path.write_text(json.dumps(value),encoding='utf-8'); return path
def base_rule(**kw):
    x={'rule_id':'RULE-1','case_id':'CASE-1','outcome_type':'diagnosis','priority':10,'blocks_fault_diagnosis':False,'required_all':[{'field':'x','op':'eq','value':1}],'required_any_groups':[],'supporting':[]}; x.update(kw); return x
def doc(rules=None): return {'rules': rules if rules is not None else [base_rule()]}
def kcase(case_id='CASE-1',physical=False): return KnowledgeCase(case_id=case_id,title='Case',domain='test',category='test',expected_label='label',intent='diagnosis',observed_patterns=('pattern',),reasoning_basis=('reason',),source_ids=('SRC-1',),support_level='direct',confidence_type='source_grounded_heuristic',implementation_status='knowledge_grounded',verification_required=True,physical_action_authorized=physical,inference_note='verify',synthetic_variation_axes=())
def klib(*cases): return CaseLibrary(version='1',cases=tuple(cases or (kcase(),)))
def prule(case_id='CASE-1',blocked=False,required_all=None,any_groups=None,supporting=None): return DiagnosticRule(rule_id='RULE-1',case_id=case_id,outcome_type='diagnosis',priority=10,blocks_fault_diagnosis=blocked,required_all=tuple(required_all or (EvidenceCondition('x','eq',1),)),required_any_groups=tuple(any_groups or ()),supporting=tuple(supporting or ()))
def eng(): return SourceGroundedDiagnosticEngine.from_files(rules_path=RULES,library_path=LIBRARY,registry_path=REGISTRY)
def test_real_rules():
    e=eng(); assert e.rule_count==16; ids={r.case_id for r in e.rules}; assert {'RO-INT-004','RO-NORM-001','RO-DATA-006'}<=ids
def test_examples():
    e=eng(); xs=json.loads((ROOT/'knowledge/diagnostic_examples.json').read_text(encoding='utf-8'))['examples']; assert len(xs)==16
    for x in xs:
        d=e.decide(x['evidence']); assert d.primary is not None; assert d.primary.case_id==x['expected_primary_case_id']; assert d.primary.source_ids; assert d.primary.verification_required is True
def test_source_ids_dedup_sorted():
    d=eng().decide({'sdi_elevated':True,'pretreatment_upset':True}); assert d.source_ids==tuple(sorted(set(d.source_ids))) and d.source_ids
def test_guard_blocks_and_wins():
    d=eng().decide({'raw_performance_change':True,'temperature_shift':True,'normalized_metrics_available':False,'flow_direction':'up','rejection_direction':'down','oxidant_exposure':True}); assert d.status=='blocked_by_guard' and d.fault_diagnosis_blocked and d.primary.case_id=='RO-NORM-001'; assert any(x.case_id=='RO-INT-004' for x in d.matches)
def test_matched_no_blocker():
    d=eng().decide({'flow_direction':'up','rejection_direction':'down','seal_issue_evidence':True}); assert d.status=='matched' and not d.fault_diagnosis_blocked and d.primary.case_id=='RO-INT-002'
def test_no_match():
    d=eng().decide({'irrelevant':True}); assert d.status=='no_supported_match' and d.primary is None and d.matches==() and d.source_ids==() and not d.fault_diagnosis_blocked
def test_supporting():
    m=eng().match({'sdi_elevated':True,'pretreatment_upset':True}); x=next(z for z in m if z.case_id=='RO-FOUL-003'); assert x.matched_fields==('sdi_elevated',) and x.supporting_fields==('pretreatment_upset',)
def test_any_group_multiple_dedupe():
    r=prule(any_groups=((EvidenceCondition('x','eq',1),EvidenceCondition('y','eq',2)),)); assert _rule_matches({'x':1,'y':2},r)==(True,('x','y'),())
def test_required_all_fail(): assert _rule_matches({'x':2},prule())==(False,(),())
def test_any_group_fail():
    r=prule(any_groups=((EvidenceCondition('y','eq',2),),)); assert _rule_matches({'x':1},r)==(False,(),())
@pytest.mark.parametrize('c,e,v',[(EvidenceCondition('x','eq',1),{'x':1},True),(EvidenceCondition('x','neq',1),{'x':2},True),(EvidenceCondition('x','in',('a','b')),{'x':'a'},True),(EvidenceCondition('x','not_in',('a','b')),{'x':'c'},True),(EvidenceCondition('x','gte',2.0),{'x':3},True),(EvidenceCondition('x','lte',2.0),{'x':2},True),(EvidenceCondition('x','exists',True),{'x':0},True),(EvidenceCondition('x','exists',False),{},True),(EvidenceCondition('x','eq',1),{},False),(EvidenceCondition('x','gte',1.0),{'x':'bad'},False),(EvidenceCondition('x','gte',1.0),{'x':True},False),(EvidenceCondition('x','gte',1.0),{'x':math.inf},False)])
def test_ops(c,e,v): assert _condition_matches(e,c) is v
def test_top_k():
    m=eng().match({'sdi_elevated':True,'pretreatment_upset':True,'source_water_change':True},top_k=1); assert len(m)==1 and m[0].case_id=='RO-FOUL-003'
@pytest.mark.parametrize('v',[0,-1,True,1.5,'1'])
def test_bad_topk(v):
    with pytest.raises(DiagnosticRuleError): eng().match({},top_k=v)
def test_evidence_dict():
    with pytest.raises(DiagnosticRuleError): eng().match([])
def test_missing_rules():
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules('missing-rules.json')
@pytest.mark.parametrize('content',['[]','{bad json'])
def test_bad_json(tmp_path,content):
    p=tmp_path/'r.json'; p.write_text(content,encoding='utf-8');
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(p)
def test_unreadable(tmp_path,monkeypatch):
    p=tmp_path/'r.json'; p.write_text('{}',encoding='utf-8'); monkeypatch.setattr(Path,'read_text',lambda *a,**k: (_ for _ in ()).throw(OSError('boom')))
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(p)
@pytest.mark.parametrize('d',[{}, {'rules':[]},{'rules':'bad'}])
def test_rules_list(tmp_path,d):
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(write_json(tmp_path/'r.json',d))
def test_rule_object(tmp_path):
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(write_json(tmp_path/'r.json',{'rules':['bad']}))
@pytest.mark.parametrize('changes',[{'rule_id':''},{'case_id':''},{'outcome_type':'bad'},{'priority':True},{'priority':1.5},{'blocks_fault_diagnosis':'yes'},{'required_all':'bad'},{'required_all':[]},{'required_any_groups':'bad'},{'required_any_groups':[[]]},{'supporting':'bad'}])
def test_rule_fields(tmp_path,changes):
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(write_json(tmp_path/'r.json',doc([base_rule(**changes)])))
@pytest.mark.parametrize('cond',['bad',{'field':'','op':'eq','value':1},{'field':'x','op':'','value':1},{'field':'x','op':'bad','value':1},{'field':'x','op':'in','value':[]},{'field':'x','op':'not_in','value':'bad'},{'field':'x','op':'gte','value':True},{'field':'x','op':'lte','value':math.inf},{'field':'x','op':'exists','value':'yes'}])
def test_condition_fields(tmp_path,cond):
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(write_json(tmp_path/'r.json',doc([base_rule(required_all=[cond])])))
def test_duplicate(tmp_path):
    with pytest.raises(DiagnosticRuleError): load_diagnostic_rules(write_json(tmp_path/'r.json',doc([base_rule(),base_rule()])))
def test_unknown_case():
    with pytest.raises(DiagnosticRuleError): SourceGroundedDiagnosticEngine(case_library=klib(),rules=(prule(case_id='UNKNOWN'),))
def test_physical_case():
    with pytest.raises(DiagnosticRuleError): SourceGroundedDiagnosticEngine(case_library=klib(kcase(physical=True)),rules=(prule(),))
def test_factory(): assert SourceGroundedDiagnosticEngine.from_files(rules_path=RULES,library_path=LIBRARY,registry_path=REGISTRY).rule_count==16

def test_valid_numeric_condition_parses(tmp_path):
    path = write_json(
        tmp_path / 'r.json',
        doc([
            base_rule(
                required_all=[
                    {'field': 'score', 'op': 'gte', 'value': 1.5}
                ]
            )
        ]),
    )
    rules = load_diagnostic_rules(path)
    assert rules[0].required_all[0].value == 1.5
