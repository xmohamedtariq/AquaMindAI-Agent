from __future__ import annotations
import json
from pathlib import Path
from src.knowledge.diagnostic_engine import SourceGroundedDiagnosticEngine
ROOT=Path(__file__).resolve().parents[1]
def test_reference_profiles():
    e=SourceGroundedDiagnosticEngine.from_files(rules_path=ROOT/'knowledge/diagnostic_rules.json',library_path=ROOT/'knowledge/case_library.json',registry_path=ROOT/'knowledge/source_registry.json')
    data=json.loads((ROOT/'knowledge/diagnostic_examples.json').read_text(encoding='utf-8')); assert data['synthetic'] is True
    for x in data['examples']:
        d=e.decide(x['evidence']); assert d.primary is not None and d.primary.case_id==x['expected_primary_case_id'] and d.primary.source_ids
        assert all(not e.case_library.get(m.case_id).physical_action_authorized for m in d.matches)
