import json
from pathlib import Path
from src.knowledge.diagnostic_engine import SourceGroundedDiagnosticEngine
ROOT=Path(__file__).resolve().parents[1]
engine=SourceGroundedDiagnosticEngine.from_files(rules_path=ROOT/'knowledge/diagnostic_rules.json',library_path=ROOT/'knowledge/case_library.json',registry_path=ROOT/'knowledge/source_registry.json')
data=json.loads((ROOT/'knowledge/scenario_matrix.json').read_text(encoding='utf-8'))
passed=0
failures=[]
for s in data['scenarios']:
 d=engine.decide(s['evidence']); actual=d.primary.case_id if d.primary else None
 if actual==s['expected_primary_case_id']: passed+=1
 else: failures.append((s['scenario_id'],s['expected_primary_case_id'],actual,d.status))
print('AquaMind Knowledge Matrix Evaluation')
print('Synthetic structured evidence only - not real plant incidents.')
print(f"Conformance: {passed}/{len(data['scenarios'])} ({passed/len(data['scenarios'])*100:.2f}%)")
if failures:
 for f in failures[:20]: print('FAIL',f)
 raise SystemExit(1)
