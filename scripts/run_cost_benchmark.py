import json
import os
from pathlib import Path
import shutil
from statistics import mean

from dotenv import load_dotenv

from src.agent.runtime import AquaMindRuntime, RuntimeConfig
from src.cost.tracker import project_task_costs
from scripts.generate_submission_traces import RUNS, _validate_result


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
KNOWLEDGE = ROOT / "knowledge"
ARTIFACTS = ROOT / "artifacts"
RUNTIME_DIR = ARTIFACTS / ".cost_runtime"
OUTPUT = ARTIFACTS / "cost_benchmark.json"


def _env_float(name: str, default: str) -> float:
    return float(os.getenv(name, default))


def _env_int(name: str, default: str) -> int:
    return int(os.getenv(name, default))


def main() -> None:
    load_dotenv()

    if not os.getenv("GEMINI_API_KEY", "").strip():
        raise RuntimeError(
            "GEMINI_API_KEY is required for the real Gemini benchmark. "
            "Keep it in .env or deployment secrets; never commit it."
        )

    usage_tier = os.getenv(
        "AQUAMIND_GEMINI_USAGE_TIER",
        "free",
    ).strip().lower()

    if usage_tier not in {"free", "paid"}:
        raise RuntimeError(
            "AQUAMIND_GEMINI_USAGE_TIER must be 'free' or 'paid'."
        )

    model = os.getenv(
        "AQUAMIND_LLM_MODEL",
        "gemini-3.5-flash-lite",
    ).strip()
    input_rate = _env_float(
        "AQUAMIND_LLM_INPUT_PER_MILLION_USD",
        "0.30",
    )
    cached_rate = _env_float(
        "AQUAMIND_LLM_CACHED_INPUT_PER_MILLION_USD",
        "0.03",
    )
    output_rate = _env_float(
        "AQUAMIND_LLM_OUTPUT_PER_MILLION_USD",
        "2.50",
    )
    max_output = _env_int(
        "AQUAMIND_LLM_MAX_OUTPUT_TOKENS",
        "160",
    )
    preflight_input = _env_int(
        "AQUAMIND_LLM_PREFLIGHT_INPUT_TOKENS",
        "6000",
    )
    budget = _env_float(
        "AQUAMIND_TASK_BUDGET_USD",
        "0.10",
    )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)

    task_results = []

    print("AquaMind Real Gemini Cost Benchmark")
    print(f"Model: {model}")
    print(f"Configured usage tier: {usage_tier}")

    for run in RUNS:
        run_dir = RUNTIME_DIR / run.task_id
        run_dir.mkdir(parents=True, exist_ok=True)

        runtime = AquaMindRuntime(
            RuntimeConfig(
                dataset_path=run.dataset,
                allowed_data_root=DATA,
                knowledge_root=KNOWLEDGE,
                memory_db_path=run_dir / "memory.db",
                audit_log_path=run_dir / "audit.jsonl",
                budget_cap_usd=budget,
                llm_enabled=True,
                llm_model=model,
                llm_input_per_million_usd=input_rate,
                llm_cached_input_per_million_usd=cached_rate,
                llm_output_per_million_usd=output_rate,
                llm_max_output_tokens=max_output,
                llm_preflight_input_tokens=preflight_input,
            )
        )

        result = runtime.run(
            task_id=f"cost-{run.task_id}",
            user_request=run.user_request,
            plant_id="cost-benchmark-plant",
        )
        _validate_result(run, result)

        summary = result["cost_summary"]
        reference_cost = summary["total_cost_usd"]
        published_free_tier_cost = (
            0.0 if usage_tier == "free" else reference_cost
        )

        task_results.append(
            {
                "task_id": run.task_id,
                "scenario": run.scenario,
                "termination_reason": result["state"].termination_reason.value,
                "tool_call_count": result["state"].tool_call_count,
                "llm_call_count": summary["call_count"],
                "input_tokens": summary["total_input_tokens"],
                "cached_input_tokens": summary["total_cached_input_tokens"],
                "output_tokens_including_thinking": summary["total_output_tokens"],
                "published_free_tier_cost_usd": published_free_tier_cost,
                "paid_tier_reference_cost_usd": reference_cost,
            }
        )

        print(
            f"PASS {run.scenario}: "
            f"llm_calls={summary['call_count']}; "
            f"free_tier=${published_free_tier_cost:.8f}; "
            f"paid_reference=${reference_cost:.8f}"
        )

    reference_costs = [
        item["paid_tier_reference_cost_usd"]
        for item in task_results
    ]
    llm_reference_costs = [
        item["paid_tier_reference_cost_usd"]
        for item in task_results
        if item["llm_call_count"] > 0
    ]

    if not llm_reference_costs or sum(llm_reference_costs) <= 0:
        raise RuntimeError(
            "No Gemini token usage was recorded. "
            "Do not generate cost_analysis.md from a zero-usage benchmark."
        )

    average_reference_all = mean(reference_costs)
    average_reference_active = mean(llm_reference_costs)

    published_average = (
        0.0
        if usage_tier == "free"
        else average_reference_all
    )

    payload = {
        "provider": "Google Gemini",
        "model": model,
        "configured_usage_tier": usage_tier,
        "pricing_verified_date": "2026-10-26",
        "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
        "published_free_tier_token_price_usd": 0.0,
        "paid_tier_reference_pricing_usd_per_million_tokens": {
            "input": input_rate,
            "cached_input": cached_rate,
            "output_including_thinking": output_rate,
        },
        "budget_cap_usd_per_task": budget,
        "budget_basis": "paid_tier_reference_equivalent",
        "tasks": task_results,
        "average_published_tier_cost_per_benchmark_task_usd": published_average,
        "average_paid_tier_reference_cost_per_all_tasks_usd": average_reference_all,
        "average_paid_tier_reference_cost_per_llm_active_task_usd": average_reference_active,
        "paid_tier_reference_projections": project_task_costs(
            average_reference_all
        ),
        "notes": [
            "Token counts come from Gemini provider-reported usage metadata, not fabricated counts.",
            "For the published Gemini Free Tier, model input/output token prices are $0 while requests stay within Free Tier limits.",
            "Free Tier quotas and rate limits can prevent high-volume execution; this report does not claim that 10,000 tasks fit inside the free quota.",
            "AquaMind enforces its $0.10 task budget using paid-tier reference-equivalent pricing so the guard remains meaningful even on the Free Tier.",
            "Safety-blocked requests can terminate before any model call and therefore use zero model tokens.",
            "Official prices and limits can change; re-check the pricing source before final submission.",
        ],
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)

    print(f"Wrote {OUTPUT}")
    print(
        "Average published-tier task cost: "
        f"${published_average:.8f}"
    )
    print(
        "Average paid-tier reference equivalent: "
        f"${average_reference_all:.8f}"
    )


if __name__ == "__main__":
    main()
