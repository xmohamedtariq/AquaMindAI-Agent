import json
from pathlib import Path
from src.knowledge.diagnostic_engine import SourceGroundedDiagnosticEngine
ROOT=Path(__file__).resolve().parents[1]
def test_all_matrix_profiles_conform():
 e=SourceGroundedDiagnosticEngine.from_files(rules_path=ROOT/'knowledge/diagnostic_rules.json',library_path=ROOT/'knowledge/case_library.json',registry_path=ROOT/'knowledge/source_registry.json')
 d=json.loads((ROOT/'knowledge/scenario_matrix.json').read_text(encoding='utf-8')); assert d['scenario_count']==720
 for s in d['scenarios']:
  decision=e.decide(s['evidence']); assert decision.primary is not None; assert decision.primary.case_id==s['expected_primary_case_id']; assert decision.primary.source_ids
