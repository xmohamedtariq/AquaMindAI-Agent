# AquaMindAI-Agent - Cost Analysis

## Provider and Model

| Item | Value |
|---|---|
| Provider | Google Gemini |
| Model | `gemini-3.5-flash-lite` |
| Usage tier | Free Tier |
| Per-task budget cap | `$0.10` |
| Pricing verified | 2026-10-31 |
| Pricing source | https://ai.google.dev/gemini-api/docs/pricing |

AquaMind records provider-reported token usage from real Gemini API calls. It does not invent or estimate token counts for completed model calls.

---

## Pricing

Current Gemini 3.5 Flash-Lite standard paid-tier reference pricing:

| Token type | USD / 1M tokens |
|---|---:|
| Input | $0.30 |
| Cached input | $0.03 |
| Output including thinking | $2.50 |

The Gemini Free Tier currently reports these token categories as free of charge while requests remain within applicable Free Tier limits.

AquaMind therefore reports:

1. actual Free Tier cost, and
2. paid-tier reference-equivalent cost for budgeting and scaling.

No Anthropic pricing is used.

---

## Cost Formula

For paid-tier reference calculations:

`cost = input_cost + cached_input_cost + output_cost`

where each component is:

`tokens / 1,000,000 x provider price`

---

## Benchmark Results

| Scenario | LLM Calls | Input | Cached | Output + Thinking | Free Tier | Paid Reference |
|---|---:|---:|---:|---:|---:|---:|
| normal_operation | 7 | 2,100 | 0 | 342 | $0.000000 | $0.001485 |
| source_grounded_fouling_investigation | 7 | 2,125 | 0 | 332 | $0.000000 | $0.0014675 |
| membrane_integrity_investigation | 1 | 207 | 0 | 39 | $0.000000 | $0.0001596 |
| recoverable_data_quality_degradation | 0 | 0 | 0 | 0 | $0.000000 | $0.000000 |
| hostile_physical_control_request | 0 | 0 | 0 | 0 | $0.000000 | $0.000000 |

Zero-call cases are valid production outcomes. For example, a safety-blocked request can terminate before any LLM call.

---

## Average Cost

**Average Free Tier benchmark cost:** `$0.000000`

**Average paid-tier reference cost per benchmark task:** `$0.00062242`

This value reflects the measured five-scenario benchmark, including zero-cost safety and fallback paths.

---

## Scaling Projection

Using the observed benchmark average:

| Tasks | Paid-Tier Reference |
|---:|---:|
| 100 | $0.062242 |
| 1,000 | $0.622420 |
| 10,000 | $6.224200 |

Free Tier availability at these volumes depends on Google's current quotas and rate limits, so AquaMind does not assume that all projected traffic remains free.

---

## Cost Controls

AquaMind enforces a per-task budget:

`budget_cap_usd = 0.10`

Cost controls include:

- preflight budget validation
- provider-reported token accounting
- input token tracking
- output and thinking token tracking
- cached-token tracking
- per-call cost calculation
- cumulative task cost
- remaining-budget calculation
- append-only audit logging

The budget guard uses paid-tier reference pricing even when the active Gemini tier is free. This keeps the budget constraint meaningful.

---

## Provider Failure and Fallback

If the Gemini API is unavailable or a quota/rate limit prevents a model call, AquaMind can use its deterministic safety-constrained planner.

The fallback:

- does not fabricate provider token usage
- does not fabricate API cost
- remains subject to the same safety and permission boundaries

---

## Limitations

- Gemini pricing and quotas may change.
- Free Tier availability is quota dependent.
- Production deployments should re-check official Google pricing.
- Benchmark datasets are synthetic and intended for project evaluation.
