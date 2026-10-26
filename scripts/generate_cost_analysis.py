import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "artifacts" / "cost_benchmark.json"
DESTINATION = ROOT / "cost_analysis.md"


def _money(value: float) -> str:
    return f"${value:.6f}"


def main() -> None:
    if not BENCHMARK.exists():
        raise FileNotFoundError(
            "Run `python -m scripts.run_cost_benchmark` first."
        )

    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    tasks = data.get("tasks", [])

    if not tasks:
        raise RuntimeError("Cost benchmark contains no tasks.")

    reference_average = float(
        data["average_paid_tier_reference_cost_per_all_tasks_usd"]
    )
    if reference_average <= 0:
        raise RuntimeError(
            "Paid-tier reference average is zero; refusing to publish "
            "a misleading cost analysis."
        )

    published_average = float(
        data["average_published_tier_cost_per_benchmark_task_usd"]
    )
    projections = data["paid_tier_reference_projections"]
    pricing = data[
        "paid_tier_reference_pricing_usd_per_million_tokens"
    ]

    task_rows = "\n".join(
        "| {scenario} | {calls} | {input} | {cached} | {output} | {free_cost} | {reference} |".format(
            scenario=item["scenario"],
            calls=item["llm_call_count"],
            input=item["input_tokens"],
            cached=item["cached_input_tokens"],
            output=item["output_tokens_including_thinking"],
            free_cost=_money(
                float(item["published_free_tier_cost_usd"])
            ),
            reference=_money(
                float(item["paid_tier_reference_cost_usd"])
            ),
        )
        for item in tasks
    )

    content = f"""# AquaMind AI — Cost Analysis

## Provider and Model

- **Provider:** {data['provider']}
- **Model:** `{data['model']}`
- **Configured usage tier:** {data['configured_usage_tier']}
- **Pricing verified:** {data['pricing_verified_date']}
- **Pricing source:** {data['pricing_source']}
- **Per-task budget cap:** {_money(float(data['budget_cap_usd_per_task']))}
- **Budget basis:** paid-tier reference-equivalent cost

The benchmark uses provider-reported Gemini token usage from real API calls. No synthetic token counts are used.

## Free Tier and Reference Pricing

Google's published Gemini Free Tier lists model input/output token prices as free of charge while requests remain inside the Free Tier limits. AquaMind therefore reports both the published Free Tier cost and a conservative paid-tier reference equivalent.

Paid-tier reference prices are USD per 1 million tokens:

| Token type | Reference price |
|---|---:|
| Input | {_money(float(pricing['input']))} |
| Cached input | {_money(float(pricing['cached_input']))} |
| Output including thinking tokens | {_money(float(pricing['output_including_thinking']))} |

## Benchmark Tasks

| Scenario | LLM calls | Input tokens | Cached input | Output + thinking | Published Free Tier cost | Paid-tier reference |
|---|---:|---:|---:|---:|---:|---:|
{task_rows}

## Average Cost

**Average published-tier benchmark cost:** {_money(published_average)}

**Average paid-tier reference equivalent per benchmark task:** {_money(reference_average)}

A safety-blocked request can terminate before any LLM call and legitimately use zero model tokens. This is included in the benchmark average because it reflects real production behavior.

## Cost Projections

The capstone requires projections for 100, 1,000, and 10,000 tasks. Free Tier availability at those volumes is quota-dependent, so AquaMind does not claim that every projected task remains free. The table below uses measured token usage with Google's paid-tier reference rates to provide an observed mixed-workload scaling estimate based on the benchmark's actual safety and provider-availability behavior.

| Volume | Paid-tier reference projection | Free Tier interpretation |
|---|---:|---|
| 100 tasks | {_money(float(projections['100_tasks_usd']))} | $0 token price while within current Free Tier quota |
| 1,000 tasks | {_money(float(projections['1000_tasks_usd']))} | quota/rate-limit dependent |
| 10,000 tasks | {_money(float(projections['10000_tasks_usd']))} | quota/rate-limit dependent; do not assume free availability |

## Cost Controls

AquaMind keeps a {_money(float(data['budget_cap_usd_per_task']))} task budget. Even when running on Gemini's Free Tier, the budget preflight uses paid-tier reference-equivalent pricing. This prevents the safety control from becoming meaningless simply because the current tier has a $0 token price.

Provider-reported usage is recorded immediately after each model call and added to the task cost ledger and append-only audit log.

If the Gemini API is unavailable or a Free Tier rate limit is reached, AquaMind falls back to its deterministic safety-constrained planner. The fallback does not fabricate token usage or provider cost.

## Limitations

- Free Tier quotas and rate limits can change and may differ by project.
- Free Tier content may be subject to Google's published data-use terms; AquaMind's benchmark uses synthetic project datasets only.
- Re-check the official pricing and quota pages before final submission or production deployment.
"""

    DESTINATION.write_text(content, encoding="utf-8")
    print(f"Wrote {DESTINATION}")


if __name__ == "__main__":
    main()

