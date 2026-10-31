# Verification Evidence

This directory contains reproducible verification evidence for AquaMindAI-Agent.

| Evidence | Verification |
|---|---|
| `tests_coverage.txt` | 572/572 tests passed with 100% source coverage |
| `memory_restart_save.txt` | Incident successfully persisted to SQLite |
| `memory_restart_verify.txt` | Incident recovered after a fresh Python process |
| `mcp_knowledge_search.txt` | Operational knowledge retrieved through the MCP client |
| `permission_layer.txt` | ASK_ON_WRITE and ALWAYS_ASK permission policies verified |
| `prompt_injection_safety.txt` | Combined injection and physical-control request blocked with SAFETY_BLOCK |
| `hostile_inputs_test.txt` | Three hostile prompt-injection inputs blocked before operational tool execution |

The primary required capstone traces remain under `traces/`.
