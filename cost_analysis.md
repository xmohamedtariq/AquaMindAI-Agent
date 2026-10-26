# AquaMind AI — Cost Analysis

## Provider and Model

- **Provider:** Google Gemini
- **Model:** `gemini-3.5-flash-lite`
- **Configured usage tier:** free
- **Pricing verified:** 2026-10-26
- **Pricing source:** https://ai.google.dev/gemini-api/docs/pricing
- **Per-task budget cap:** $0.100000
- **Budget basis:** paid-tier reference-equivalent cost

The benchmark uses provider-reported Gemini token usage from real API calls. No synthetic token counts are used.

## Free Tier and Reference Pricing

Google's published Gemini Free Tier lists model input/output token prices as free of charge while requests remain inside the Free Tier limits. AquaMind therefore reports both the published Free Tier cost and a conservative paid-tier reference equivalent.

Paid-tier reference prices are USD per 1 million tokens:

| Token type | Reference price |
|---|---:|
| Input | $0.300000 |
| Cached input | $0.030000 |
| Output including thinking tokens | $2.500000 |

## Benchmark Tasks

| Scenario | LLM calls | Input tokens | Cached input | Output + thinking | Published Free Tier cost | Paid-tier reference |
|---|---:|---:|---:|---:|---:|---:|
| normal_operation | 7 | 2100 | 0 | 342 | $0.000000 | $0.001485 |
| source_grounded_fouling_investigation | 7 | 2125 | 0 | 332 | $0.000000 | $0.001468 |
| membrane_integrity_investigation | 1 | 207 | 0 | 39 | $0.000000 | $0.000160 |
| recoverable_data_quality_degradation | 0 | 0 | 0 | 0 | $0.000000 | $0.000000 |
| hostile_physical_control_request | 0 | 0 | 0 | 0 | $0.000000 | $0.000000 |

## Average Cost

**Average published-tier benchmark cost:** $0.000000

**Average paid-tier reference equivalent per benchmark task:** $0.000622

A safety-blocked request can terminate before any LLM call and legitimately use zero model tokens. This is included in the benchmark average because it reflects real production behavior.

## Cost Projections

The capstone requires projections for 100, 1,000, and 10,000 tasks. Free Tier availability at those volumes is quota-dependent, so AquaMind does not claim that every projected task remains free. The table below uses measured token usage with Google's paid-tier reference rates to provide an observed mixed-workload scaling estimate based on the benchmark's actual safety and provider-availability behavior.

| Volume | Paid-tier reference projection | Free Tier interpretation |
|---|---:|---|
| 100 tasks | $0.062242 | $0 token price while within current Free Tier quota |
| 1,000 tasks | $0.622420 | quota/rate-limit dependent |
| 10,000 tasks | $6.224200 | quota/rate-limit dependent; do not assume free availability |

## Cost Controls

AquaMind keeps a $0.100000 task budget. Even when running on Gemini's Free Tier, the budget preflight uses paid-tier reference-equivalent pricing. This prevents the safety control from becoming meaningless simply because the current tier has a $0 token price.

Provider-reported usage is recorded immediately after each model call and added to the task cost ledger and append-only audit log.

If the Gemini API is unavailable or a Free Tier rate limit is reached, AquaMind falls back to its deterministic safety-constrained planner. The fallback does not fabricate token usage or provider cost.

## Limitations

- Free Tier quotas and rate limits can change and may differ by project.
- Free Tier content may be subject to Google's published data-use terms; AquaMind's benchmark uses synthetic project datasets only.
- Re-check the official pricing and quota pages before final submission or production deployment.
