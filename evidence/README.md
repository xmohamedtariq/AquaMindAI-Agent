# Verification Evidence

This directory contains reproducible evidence generated from the AquaMindAI-Agent implementation.

| Evidence | Verification |
|---|---|
| `tests_coverage.txt` | 572/572 tests passed with 100% source coverage |
| `memory_restart_save.txt` | Incident successfully persisted to SQLite |
| `memory_restart_verify.txt` | Incident recovered from a fresh Python process |
| `mcp_knowledge_search.txt` | Operational knowledge retrieved through the MCP client |
| `permission_layer.txt` | ASK_ON_WRITE and ALWAYS_ASK permission policies verified |
| `prompt_injection_safety.txt` | Prompt injection and physical-control request blocked with SAFETY_BLOCK before any operational tool call |

These files are supporting verification artifacts. The primary required traces remain under `traces/`.
