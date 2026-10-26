# AquaMind Hybrid Gemini Reasoning and Cost Integration

## Purpose

AquaMind uses a hybrid single-agent production pattern:

1. The deterministic policy planner selects the next safety-approved operational action.
2. An optional Gemini reasoning layer produces the concise public `decision_summary` for that already-approved candidate.
3. Gemini cannot create tools, change permissions, authorize plant actuation, or bypass the request-boundary safety guard.
4. If Gemini is unavailable or rate-limited, AquaMind falls back to the deterministic planner and records no fabricated model usage.

This preserves AquaMindAI-Agent's single-agent architecture while adding real model-backed reasoning and provider-reported token accounting.

## Default Model

- Provider: Google Gemini Developer API
- Model: `gemini-3.5-flash-lite`
- Model status: stable
- Pricing verified: 2026-10-26
- Published Free Tier input/output token price: free of charge while within Free Tier limits
- Paid-tier reference input: $0.30 / 1M tokens
- Paid-tier reference cached input: $0.03 / 1M tokens
- Paid-tier reference output (including thinking tokens): $2.50 / 1M tokens
- Pricing source: https://ai.google.dev/gemini-api/docs/pricing

Pricing is configurable because provider rates can change.

## Cost Safety

Before each reasoning call, the hybrid planner performs a conservative budget preflight using the paid-tier reference pricing, even when the project is on the Free Tier. After a real Gemini call, AquaMind records provider-reported prompt, cached-input, candidate-output, and thinking-token usage. Candidate output plus thinking tokens are counted as output for the paid-tier reference calculation.

The AquaMindAI-Agent task budget remains $0.10 per task.

## Free Tier Reporting

The benchmark reports two values:

- **Published Free Tier cost:** $0 token price while requests remain within the Free Tier limits.
- **Paid-tier reference equivalent:** measured usage multiplied by current paid-tier prices, used for conservative scaling projections and budget preflight.

AquaMind does not claim that 1,000 or 10,000 tasks necessarily fit inside Free Tier quotas.

## Secrets

`GEMINI_API_KEY` must be stored in a local `.env` file, the current PowerShell environment, or a deployment secret manager. It must never be committed to Git.

## Data Privacy Boundary

The benchmark uses AquaMind's synthetic datasets. Do not send real plant-sensitive telemetry through a Free Tier account without reviewing the provider's current data-use terms and organizational requirements.

## Real Benchmark

After setting `GEMINI_API_KEY` locally:

```powershell
python -m scripts.run_cost_benchmark
python -m scripts.generate_cost_analysis
```

The first command runs the official benchmark scenarios with real Gemini calls and writes `artifacts/cost_benchmark.json`. The second generates the required `cost_analysis.md` using measured token usage.
