from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


TOKENS_PER_MILLION = Decimal("1000000")


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _non_negative_decimal(
    value: Any,
    field_name: str,
) -> Decimal:
    """Convert a numeric value to a finite non-negative Decimal."""

    try:
        result = Decimal(
            str(value)
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ) as exc:
        raise ValueError(
            f"{field_name} must be numeric."
        ) from exc

    if not result.is_finite():
        raise ValueError(
            f"{field_name} must be finite."
        )

    if result < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return result


def _positive_decimal(
    value: Any,
    field_name: str,
) -> Decimal:
    """Convert a numeric value to a finite positive Decimal."""

    result = _non_negative_decimal(
        value,
        field_name,
    )

    if result == 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return result


def _token_count(
    value: Any,
    field_name: str,
) -> int:
    """Validate a token count."""

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        raise TypeError(
            f"{field_name} must be an integer."
        )

    if value < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return value


@dataclass(frozen=True)
class ModelPricing:
    """
    Token pricing for one LLM model.

    Rates are expressed in USD per one million tokens.
    """

    model: str
    input_per_million_usd: Decimal | float | str
    output_per_million_usd: Decimal | float | str
    cached_input_per_million_usd: Decimal | float | str | None = None

    def __post_init__(
        self,
    ) -> None:

        if (
            not isinstance(
                self.model,
                str,
            )
            or not self.model.strip()
        ):
            raise ValueError(
                "model is required."
            )

        object.__setattr__(
            self,
            "model",
            self.model.strip(),
        )

        object.__setattr__(
            self,
            "input_per_million_usd",
            _non_negative_decimal(
                self.input_per_million_usd,
                "input_per_million_usd",
            ),
        )

        object.__setattr__(
            self,
            "output_per_million_usd",
            _non_negative_decimal(
                self.output_per_million_usd,
                "output_per_million_usd",
            ),
        )

        cached_rate = (
            self.input_per_million_usd
            if self.cached_input_per_million_usd is None
            else _non_negative_decimal(
                self.cached_input_per_million_usd,
                "cached_input_per_million_usd",
            )
        )

        object.__setattr__(
            self,
            "cached_input_per_million_usd",
            cached_rate,
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return JSON-safe pricing information."""

        return {
            "model":
                self.model,
            "input_per_million_usd":
                float(
                    self.input_per_million_usd
                ),
            "output_per_million_usd":
                float(
                    self.output_per_million_usd
                ),
            "cached_input_per_million_usd":
                float(
                    self.cached_input_per_million_usd
                ),
        }


def calculate_usage_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    pricing: ModelPricing,
    cached_input_tokens: int = 0,
) -> Decimal:
    """Calculate the exact cost of one model call."""

    validated_input = _token_count(
        input_tokens,
        "input_tokens",
    )

    validated_output = _token_count(
        output_tokens,
        "output_tokens",
    )

    validated_cached = _token_count(
        cached_input_tokens,
        "cached_input_tokens",
    )

    if validated_cached > validated_input:
        raise ValueError(
            "cached_input_tokens cannot exceed input_tokens."
        )

    uncached_input = (
        validated_input
        - validated_cached
    )

    input_cost = (
        Decimal(uncached_input)
        * pricing.input_per_million_usd
        / TOKENS_PER_MILLION
    )

    cached_input_cost = (
        Decimal(validated_cached)
        * pricing.cached_input_per_million_usd
        / TOKENS_PER_MILLION
    )

    output_cost = (
        Decimal(validated_output)
        * pricing.output_per_million_usd
        / TOKENS_PER_MILLION
    )

    return (
        input_cost
        + cached_input_cost
        + output_cost
    )


def project_task_costs(
    average_task_cost_usd: Any,
) -> dict[str, float]:
    """
    Produce the projections required by cost_analysis.md.

    Projections cover 100, 1,000 and 10,000 tasks.
    """

    average = _non_negative_decimal(
        average_task_cost_usd,
        "average_task_cost_usd",
    )

    return {
        "average_cost_per_task_usd":
            float(
                average
            ),
        "100_tasks_usd":
            float(
                average
                * Decimal("100")
            ),
        "1000_tasks_usd":
            float(
                average
                * Decimal("1000")
            ),
        "10000_tasks_usd":
            float(
                average
                * Decimal("10000")
            ),
    }


class CostTracker:
    """
    Real-time per-task LLM cost tracker.

    Pricing is deliberately configurable rather than
    hard-coded so AquaMind can use the official pricing
    of the selected model/provider at deployment time.
    """

    def __init__(
        self,
        *,
        budget_cap_usd: Any,
        pricing: Iterable[
            ModelPricing
        ] | None = None,
    ) -> None:

        self.budget_cap_usd = (
            _positive_decimal(
                budget_cap_usd,
                "budget_cap_usd",
            )
        )

        self._pricing: dict[
            str,
            ModelPricing,
        ] = {}

        self._events: list[
            dict[str, Any]
        ] = []

        self._total_cost_usd = (
            Decimal("0")
        )

        if pricing is not None:
            for item in pricing:
                self.register_pricing(
                    item
                )

    def register_pricing(
        self,
        pricing: ModelPricing,
    ) -> None:
        """Register or replace pricing for one model."""

        if not isinstance(
            pricing,
            ModelPricing,
        ):
            raise TypeError(
                (
                    "pricing must be a "
                    "ModelPricing instance."
                )
            )

        self._pricing[
            pricing.model
        ] = pricing

    def pricing_for(
        self,
        model: str,
    ) -> ModelPricing:
        """Return configured pricing for a model."""

        normalized = model.strip()

        if normalized not in self._pricing:
            raise KeyError(
                (
                    "No pricing is configured "
                    f"for model: {normalized}"
                )
            )

        return self._pricing[
            normalized
        ]

    @property
    def total_cost_usd(
        self,
    ) -> Decimal:
        """Return accumulated task cost."""

        return self._total_cost_usd

    @property
    def remaining_budget_usd(
        self,
    ) -> Decimal:
        """Return remaining task budget, never below zero."""

        remaining = (
            self.budget_cap_usd
            - self._total_cost_usd
        )

        return max(
            Decimal("0"),
            remaining,
        )

    @property
    def budget_exhausted(
        self,
    ) -> bool:
        """Return True once task cost reaches the cap."""

        return (
            self._total_cost_usd
            >= self.budget_cap_usd
        )

    def estimate_usage_cost(
        self,
        *,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
    ) -> Decimal:
        """Estimate a model call without mutating state."""

        pricing = self.pricing_for(
            model
        )

        return calculate_usage_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=pricing,
            cached_input_tokens=cached_input_tokens,
        )

    def can_afford(
        self,
        *,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
    ) -> bool:
        """Check whether an estimated call fits the budget."""

        estimated = (
            self.estimate_usage_cost(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_input_tokens=cached_input_tokens,
            )
        )

        return (
            self._total_cost_usd
            + estimated
            <= self.budget_cap_usd
        )

    def record_usage(
        self,
        *,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        operation: str = "llm_call",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """
        Record one real model usage event.

        The tracker updates task cost immediately after
        usage is reported by the model provider.
        """

        if not operation.strip():
            raise ValueError(
                "operation is required."
            )

        validated_input = _token_count(
            input_tokens,
            "input_tokens",
        )

        validated_output = _token_count(
            output_tokens,
            "output_tokens",
        )

        validated_cached = _token_count(
            cached_input_tokens,
            "cached_input_tokens",
        )

        pricing = self.pricing_for(
            model
        )

        call_cost = (
            calculate_usage_cost(
                input_tokens=validated_input,
                output_tokens=validated_output,
                pricing=pricing,
                cached_input_tokens=validated_cached,
            )
        )

        self._total_cost_usd += (
            call_cost
        )

        event = {
            "timestamp":
                timestamp
                or _utc_now(),
            "operation":
                operation.strip(),
            "model":
                pricing.model,
            "input_tokens":
                validated_input,
            "output_tokens":
                validated_output,
            "cached_input_tokens":
                validated_cached,
            "input_per_million_usd":
                float(
                    pricing
                    .input_per_million_usd
                ),
            "output_per_million_usd":
                float(
                    pricing
                    .output_per_million_usd
                ),
            "cached_input_per_million_usd":
                float(
                    pricing
                    .cached_input_per_million_usd
                ),
            "call_cost_usd":
                float(
                    call_cost
                ),
            "task_total_usd":
                float(
                    self._total_cost_usd
                ),
            "budget_cap_usd":
                float(
                    self.budget_cap_usd
                ),
            "budget_remaining_usd":
                float(
                    self.remaining_budget_usd
                ),
            "budget_exhausted":
                self.budget_exhausted,
            "within_budget":
                (
                    self._total_cost_usd
                    <= self.budget_cap_usd
                ),
        }

        self._events.append(
            event
        )

        return dict(
            event
        )

    def events(
        self,
    ) -> list[dict[str, Any]]:
        """Return a defensive copy of usage history."""

        return [
            dict(event)
            for event in self._events
        ]

    def summary(
        self,
    ) -> dict[str, Any]:
        """Return current task-level cost statistics."""

        total_input_tokens = sum(
            event["input_tokens"]
            for event in self._events
        )

        total_output_tokens = sum(
            event["output_tokens"]
            for event in self._events
        )

        total_cached_input_tokens = sum(
            event["cached_input_tokens"]
            for event in self._events
        )

        call_count = len(
            self._events
        )

        average_call_cost = (
            self._total_cost_usd
            / Decimal(
                max(
                    call_count,
                    1,
                )
            )
        )

        return {
            "call_count":
                call_count,
            "total_input_tokens":
                total_input_tokens,
            "total_output_tokens":
                total_output_tokens,
            "total_cached_input_tokens":
                total_cached_input_tokens,
            "total_cost_usd":
                float(
                    self._total_cost_usd
                ),
            "average_call_cost_usd":
                float(
                    average_call_cost
                ),
            "budget_cap_usd":
                float(
                    self.budget_cap_usd
                ),
            "budget_remaining_usd":
                float(
                    self.remaining_budget_usd
                ),
            "budget_exhausted":
                self.budget_exhausted,
        }