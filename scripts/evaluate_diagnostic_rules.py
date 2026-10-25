from __future__ import annotations
import json
from pathlib import Path
from src.knowledge.diagnostic_engine import SourceGroundedDiagnosticEngine
ROOT=Path(__file__).resolve().parents[1]
def main()->None:
    engine=SourceGroundedDiagnosticEngine.from_files(rules_path=ROOT/'knowledge/diagnostic_rules.json',library_path=ROOT/'knowledge/case_library.json',registry_path=ROOT/'knowledge/source_registry.json')
    examples=json.loads((ROOT/'knowledge/diagnostic_examples.json').read_text(encoding='utf-8'))['examples']
    print('\nAquaMind Source-Grounded Diagnostic Rule Evaluation')
    print('Synthetic evidence profiles only - not real plant incidents.\n')
    passed=0
    for example in examples:
        decision=engine.decide(example['evidence'])
        actual=decision.primary.case_id if decision.primary is not None else None
        expected=example['expected_primary_case_id']
        result='PASS' if actual==expected else 'FAIL'
        passed += int(result=='PASS')
        print(f"{example['example_id']}: expected={expected} actual={actual} status={decision.status} {result}")
    print(f"\nConformance: {passed}/{len(examples)} ({passed/len(examples)*100:.2f}%)")
    if passed != len(examples): raise SystemExit(1)
if __name__=='__main__': main()
