import pytest
from src.knowledge.diagnostic_engine import DiagnosticRule, EvidenceCondition, load_diagnostic_rules
from src.knowledge.scenario_generator import _materialize, materialize_rule, generate_rule_scenarios
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_real_rules_generate_eight_each():
 rules=load_diagnostic_rules(ROOT/'knowledge/diagnostic_rules.json'); assert len(rules)==90
 items=[s for r in rules for s in generate_rule_scenarios(r)]; assert len(items)==720; assert all(x.synthetic for x in items)
def test_materialize_all_supported_ops():
 for c,expected in [
 (EvidenceCondition('x','eq',1),1),(EvidenceCondition('x','in',('a','b')),'a'),(EvidenceCondition('x','neq',1),'__different__'),
 (EvidenceCondition('x','not_in',('a',)),'__outside__'),(EvidenceCondition('x','gte',2.0),2.0),(EvidenceCondition('x','lte',2.0),2.0),
 (EvidenceCondition('x','exists',True),'present'),(EvidenceCondition('x','exists',False),None)]: assert _materialize(c)==expected
 with pytest.raises(ValueError): _materialize(EvidenceCondition('x','bad',1))
def test_materialize_any_group_and_support():
 r=DiagnosticRule('R','C','risk',1,False,(EvidenceCondition('a','eq',True),),((EvidenceCondition('b','eq',1),EvidenceCondition('c','eq',2)),),(EvidenceCondition('d','eq',3),))
 assert materialize_rule(r,any_choice=9,include_support=True)=={'a':True,'c':2,'d':3}
 assert len(generate_rule_scenarios(r,variations=10))==10
@pytest.mark.parametrize('value',[0,-1,True,1.5,'8'])
def test_invalid_variation_count(value):
 r=DiagnosticRule('R','C','risk',1,False,(EvidenceCondition('a','eq',True),),(),())
 with pytest.raises(ValueError): generate_rule_scenarios(r,variations=value)
