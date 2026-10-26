from collections.abc import Callable
from typing import Any

from src.agent.planner import AgentAction, PlanDecision, Planner
from src.agent.state import AgentState, TerminationReason


UsageRecorder = Callable[[AgentState, dict[str, Any]], None]
BudgetGuard = Callable[[AgentState, str, int, int], bool]
FallbackLogger = Callable[[AgentState, Exception], None]


class HybridPlanner(Planner):
    """
    Deterministic policy planner with an optional LLM reasoning layer.

    Tool selection remains deterministic and safety-constrained. The LLM
    can only provide the public decision summary for the already-approved
    candidate action. If the model is unavailable, AquaMind falls back to
    the deterministic reason without interrupting the investigation.
    """

    def __init__(
        self,
        *,
        reasoner: Any,
        usage_recorder: UsageRecorder,
        budget_guard: BudgetGuard | None = None,
        fallback_logger: FallbackLogger | None = None,
        model: str = "gemini-3.5-flash-lite",
        preflight_input_tokens: int = 6000,
        max_output_tokens: int = 160,
    ) -> None:
        self.reasoner = reasoner
        self.usage_recorder = usage_recorder
        self.budget_guard = budget_guard
        self.fallback_logger = fallback_logger
        self.model = model
        self.preflight_input_tokens = preflight_input_tokens
        self.max_output_tokens = max_output_tokens

    def next_action(self, state: AgentState) -> PlanDecision:
        deterministic = super().next_action(state)

        if deterministic.action in {
            AgentAction.STOP,
            AgentAction.FINALIZE,
        }:
            return deterministic

        if self.budget_guard is not None and not self.budget_guard(
            state,
            self.model,
            self.preflight_input_tokens,
            self.max_output_tokens,
        ):
            return PlanDecision(
                action=AgentAction.STOP,
                reason=(
                    "The remaining task budget is below the conservative "
                    "preflight allowance required for the next LLM "
                    "reasoning call."
                ),
                termination_reason=TerminationReason.BUDGET_LIMIT_REACHED,
            )

        try:
            result = self.reasoner.review_candidate(
                state=state,
                candidate_action=deterministic.action.value,
                fallback_reason=deterministic.reason,
            )
        except Exception as exc:
            if self.fallback_logger is not None:
                self.fallback_logger(state, exc)

            return deterministic

        self.usage_recorder(state, result.usage)

        return PlanDecision(
            action=deterministic.action,
            reason=result.decision_summary,
            termination_reason=deterministic.termination_reason,
        )
