# Verification Evidence

This directory contains reproducible verification evidence for AquaMindAI-Agent.

| Evidence | Verification |
|---|---|
| `tests_coverage.txt` | 572/572 tests passed with 100% source coverage |
| `memory_restart_save.txt` | Incident successfully persisted to SQLite |
| `memory_restart_verify.txt` | Incident recovered after a fresh Python process |
| `mcp_knowledge_search.txt` | Operational knowledge retrieved through the MCP client |
| `mcp_runtime_resolution.txt` | Official `mcp==2.3.0` SDK resolution verified from installed `site-packages` |
| `mcp_protocol_end_to_end.txt` | MCP client/server tool and resource workflow verified end to end |
| `max_turns_failure_generation.txt` | Reproducible MAX_TURNS task-failure generation result |
| `max_turns_failure_audit.jsonl` | Seven-event hash-chained task-failure audit snapshot with verified integrity |
| `permission_layer.txt` | ASK_ON_WRITE and ALWAYS_ASK permission policies verified |
| `prompt_injection_safety.txt` | Combined injection and physical-control request blocked with SAFETY_BLOCK |
| `hostile_inputs_test.txt` | Three hostile prompt-injection inputs blocked before operational tool execution |

The primary capstone traces remain under `traces/`.

The safety-block trace is `traces/explicit_failure.jsonl`. Its filename is retained for compatibility, but its `SAFETY_BLOCK` outcome represents successful safety enforcement.

The genuine reproducible task-failure case is `traces/max_turns_failure.jsonl`, which terminates with `MAX_TURNS_REACHED` after two successful operational tool calls.
