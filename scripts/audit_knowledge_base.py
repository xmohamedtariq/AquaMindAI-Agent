from pathlib import Path
from src.knowledge.source_audit import audit_knowledge_base
ROOT=Path(__file__).resolve().parents[1]
summary=audit_knowledge_base(
 registry_path=ROOT/'knowledge/source_registry.json', case_library_path=ROOT/'knowledge/case_library.json',
 rules_path=ROOT/'knowledge/diagnostic_rules.json', vocabulary_path=ROOT/'knowledge/evidence_vocabulary.json',
 scenario_matrix_path=ROOT/'knowledge/scenario_matrix.json')
print('AquaMind Knowledge Base Audit')
print(f'Sources: {summary.source_count}')
print(f'Cases: {summary.case_count}')
print(f'Rules: {summary.rule_count}')
print(f'Evidence terms: {summary.vocabulary_count}')
print(f'Synthetic scenarios: {summary.scenario_count}')
print('Draft sources:', ', '.join(summary.draft_source_ids) or 'none')
print('Unused sources:', ', '.join(summary.unused_source_ids) or 'none')
