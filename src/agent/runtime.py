import asyncio
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agent.hybrid_planner import HybridPlanner
from src.agent.loop import AgentLoop
from src.agent.planner import Planner
from src.agent.state import (
    AgentState,
    TerminationReason,
)
from src.audit.logger import AuditLogger
from src.cost.tracker import (
    CostTracker,
    ModelPricing,
)
from src.knowledge.diagnostic_engine import (
    SourceGroundedDiagnosticEngine,
)
from src.knowledge.runtime_grounding import (
    make_source_grounded_diagnosis,
)
from src.mcp.client import (
    OperationalKnowledgeClient,
)
from src.mcp.server import create_mcp_server
from src.llm.gemini_reasoner import GeminiReasoner
from src.memory.sqlite_memory import (
    IncidentMemory,
    make_save_incident,
    make_search_incident_memory,
)
from src.safety.injection_guard import (
    guard_agent_request,
)
from src.safety.permissions import (
    make_permission_guard,
)
from src.tools.anomaly_detection import (
    make_detect_anomalies,
)
from src.tools.diagnosis import (
    make_diagnose_issue,
)
from src.tools.kpi_tools import (
    make_calculate_plant_kpis,
)
from src.tools.reporting import (
    make_generate_incident_report,
)
from src.tools.validation import (
    make_validate_sensor_data,
)


ToolFunction = Callable[
    [AgentState],
    Any,
]


@dataclass(frozen=True)
class RuntimeConfig:
    """
    Configuration for one AquaMind investigation runtime.

    One runtime instance is intended to represent
    one task-level cost budget.
    """

    dataset_path: str | Path
    allowed_data_root: str | Path = "data"

    knowledge_root: str | Path = "knowledge"

    memory_db_path: str | Path = (
        "data/aquamind_memory.db"
    )

    audit_log_path: str | Path = (
        "logs/aquamind_audit.jsonl"
    )

    knowledge_limit: int = 5
    budget_cap_usd: float = 0.10

    case_library_path: str | Path | None = None
    source_registry_path: str | Path | None = None
    diagnostic_rules_path: str | Path | None = None
    evidence_vocabulary_path: str | Path | None = None
    diagnostic_top_k: int = 5

    llm_enabled: bool = False
    llm_model: str = "gemini-3.5-flash-lite"
    llm_input_per_million_usd: float = 0.30
    llm_cached_input_per_million_usd: float = 0.03
    llm_output_per_million_usd: float = 2.50
    llm_max_output_tokens: int = 160
    llm_preflight_input_tokens: int = 6000


class AquaMindRuntime:
    """
    Production integration layer for AquaMind AI.

    Integrates:

    - request-boundary safety,
    - autonomous AgentLoop,
    - analytical tools,
    - MCP operational knowledge,
    - SQLite incident memory,
    - permission enforcement,
    - append-only audit logging,
    - real-time model cost tracking,
    - structured incident reporting.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        *,
        pricing: Iterable[
            ModelPricing
        ] | None = None,
        knowledge_client: Any | None = None,
        memory: IncidentMemory | None = None,
        audit_logger: AuditLogger | None = None,
        cost_tracker: CostTracker | None = None,
        diagnostic_engine: SourceGroundedDiagnosticEngine | None = None,
        reasoner: Any | None = None,
    ) -> None:

        self.config = config

        if memory is None:
            self.memory = IncidentMemory(
                config.memory_db_path
            )
        else:
            self.memory = memory

        if audit_logger is None:
            self.audit_logger = AuditLogger(
                config.audit_log_path
            )
        else:
            self.audit_logger = (
                audit_logger
            )

        if cost_tracker is None:
            self.cost_tracker = CostTracker(
                budget_cap_usd=(
                    config.budget_cap_usd
                ),
                pricing=pricing,
            )
        else:
            self.cost_tracker = (
                cost_tracker
            )

        if config.llm_enabled:
            self.cost_tracker.register_pricing(
                ModelPricing(
                    model=config.llm_model,
                    input_per_million_usd=(
                        config.llm_input_per_million_usd
                    ),
                    cached_input_per_million_usd=(
                        config.llm_cached_input_per_million_usd
                    ),
                    output_per_million_usd=(
                        config.llm_output_per_million_usd
                    ),
                )
            )

        if knowledge_client is None:
            mcp_server = create_mcp_server(
                config.knowledge_root
            )

            self.knowledge_client = (
                OperationalKnowledgeClient(
                    mcp_server
                )
            )

        else:
            self.knowledge_client = (
                knowledge_client
            )

        self.case_library_path = (
            self._knowledge_path(
                config.case_library_path,
                config.knowledge_root,
                "case_library.json",
            )
        )
        self.source_registry_path = (
            self._knowledge_path(
                config.source_registry_path,
                config.knowledge_root,
                "source_registry.json",
            )
        )
        self.diagnostic_rules_path = (
            self._knowledge_path(
                config.diagnostic_rules_path,
                config.knowledge_root,
                "diagnostic_rules.json",
            )
        )
        self.evidence_vocabulary_path = (
            self._knowledge_path(
                config.evidence_vocabulary_path,
                config.knowledge_root,
                "evidence_vocabulary.json",
            )
        )

        if diagnostic_engine is None:
            self.diagnostic_engine = (
                SourceGroundedDiagnosticEngine
                .from_files(
                    rules_path=(
                        self.diagnostic_rules_path
                    ),
                    library_path=(
                        self.case_library_path
                    ),
                    registry_path=(
                        self.source_registry_path
                    ),
                )
            )
        else:
            self.diagnostic_engine = (
                diagnostic_engine
            )

        self.tools = (
            self._build_tool_registry()
        )

        planner = self._build_planner(
            reasoner=reasoner
        )

        self.agent_loop = AgentLoop(
            tools=self.tools,
            planner=planner,
        )

    def _build_planner(
        self,
        *,
        reasoner: Any | None,
    ) -> Planner:
        """Build deterministic or hybrid LLM-assisted planning."""

        if not self.config.llm_enabled:
            return Planner()

        if reasoner is None:
            reasoner = GeminiReasoner(
                model=self.config.llm_model,
                max_output_tokens=(
                    self.config.llm_max_output_tokens
                ),
            )

        return HybridPlanner(
            reasoner=reasoner,
            usage_recorder=(
                self._record_reasoning_usage
            ),
            budget_guard=(
                self._can_afford_reasoning
            ),
            fallback_logger=(
                self._log_reasoning_fallback
            ),
            model=self.config.llm_model,
            preflight_input_tokens=(
                self.config.llm_preflight_input_tokens
            ),
            max_output_tokens=(
                self.config.llm_max_output_tokens
            ),
        )

    def _can_afford_reasoning(
        self,
        state: AgentState,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> bool:
        """Conservatively preflight one model reasoning call."""

        if state.budget_exceeded():
            return False

        return self.cost_tracker.can_afford(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=0,
        )

    def _record_reasoning_usage(
        self,
        state: AgentState,
        usage: dict[str, Any],
    ) -> None:
        """Record provider-reported usage from the LLM reasoner."""

        self._apply_usage(
            state=state,
            tool_name="llm_reasoning",
            observation={
                "_usage": dict(usage)
            },
        )

    def _log_reasoning_fallback(
        self,
        state: AgentState,
        exc: Exception,
    ) -> None:
        """Audit a model failure before deterministic fallback."""

        self.audit_logger.log_event(
            task_id=state.task_id,
            event_type="llm_reasoning",
            action="fallback_to_deterministic_planner",
            status="fallback",
            details={
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
        )

    @staticmethod
    def _knowledge_path(
        configured: str | Path | None,
        knowledge_root: str | Path,
        filename: str,
    ) -> Path:
        """Resolve an optional knowledge file path."""

        if configured is not None:
            return Path(configured)

        return Path(knowledge_root) / filename

    @staticmethod
    def _run_async(
        awaitable: Any,
    ) -> Any:
        """
        Run one asynchronous MCP operation from
        AquaMind's synchronous AgentLoop.
        """

        return asyncio.run(
            awaitable
        )

    @staticmethod
    def _observation_status(
        observation: Any,
    ) -> str:
        """Classify a tool result for audit logging."""

        if not isinstance(
            observation,
            dict,
        ):
            return "success"

        if (
            observation.get(
                "_safety_violation"
            )
            or observation.get(
                "_safety_blocked"
            )
        ):
            return "blocked"

        if observation.get(
            "_permission_required"
        ):
            return "approval_required"

        if (
            observation.get(
                "success"
            )
            is False
        ):
            return "failed"

        return "success"

    @staticmethod
    def _observation_summary(
        observation: Any,
    ) -> dict[str, Any]:
        """
        Produce a compact audit-safe result summary.

        Full operational records are deliberately not
        duplicated into the audit log.
        """

        if not isinstance(
            observation,
            dict,
        ):
            return {
                "result_type":
                    type(
                        observation
                    ).__name__,
            }

        summary: dict[
            str,
            Any,
        ] = {
            "keys": sorted(
                str(key)
                for key
                in observation
            )
        }

        useful_keys = (
            "success",
            "recoverable",
            "error",
            "message",
            "row_count",
            "match_count",
            "diagnosis_status",
            "permission_level",
        )

        for key in useful_keys:
            if key in observation:
                summary[key] = (
                    observation[
                        key
                    ]
                )

        return summary

    @staticmethod
    def _final_answer_from_report(
        report: dict[str, Any],
    ) -> str:
        """Create the user-facing completion message."""

        summary = report.get(
            "executive_summary"
        )

        if not isinstance(
            summary,
            str,
        ) or not summary.strip():
            summary = (
                "AquaMind AI completed the "
                "desalination plant investigation."
            )

        recommendations = (
            report.get(
                "recommendations"
            )
        )

        clean_recommendations: list[
            str
        ] = []

        if isinstance(
            recommendations,
            list,
        ):
            clean_recommendations = [
                item.strip()
                for item in recommendations
                if (
                    isinstance(
                        item,
                        str,
                    )
                    and item.strip()
                )
            ]

        if not clean_recommendations:
            return summary

        recommendation_text = "; ".join(
            clean_recommendations[
                :3
            ]
        )

        return (
            f"{summary} "
            "Recommended verification: "
            f"{recommendation_text}"
        )

    @staticmethod
    def _latest_report(
        state: AgentState,
    ) -> dict[str, Any] | None:
        """Return the latest generated incident report."""

        for observation in reversed(
            state.observations
        ):

            if (
                observation.get(
                    "source"
                )
                != "generate_incident_report"
            ):
                continue

            content = observation.get(
                "content"
            )

            if not isinstance(
                content,
                dict,
            ):
                continue

            report = content.get(
                "report"
            )

            if isinstance(
                report,
                dict,
            ):
                return report

        return None

    def _search_operational_knowledge(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        """
        Search curated desalination knowledge
        through the actual MCP client.
        """

        return self._run_async(
            self.knowledge_client.search(
                state.user_request,
                limit=(
                    self.config
                    .knowledge_limit
                ),
            )
        )

    def _make_report_tool(
        self,
    ) -> ToolFunction:
        """
        Wrap structured reporting so the report's
        conclusion becomes the final agent answer.
        """

        base_tool = (
            make_generate_incident_report()
        )

        def tool(
            state: AgentState,
        ) -> dict[str, Any]:

            result = base_tool(
                state
            )

            if (
                result.get(
                    "success"
                )
                is True
            ):
                report = result.get(
                    "report"
                )

                if isinstance(
                    report,
                    dict,
                ):
                    state.final_answer = (
                        self
                        ._final_answer_from_report(
                            report
                        )
                    )

            return result

        return tool

    def _apply_usage(
        self,
        *,
        state: AgentState,
        tool_name: str,
        observation: Any,
    ) -> None:
        """
        Apply provider-reported model usage in real time.

        Any future LLM-backed tool can return:

        {
            "_usage": {
                "model": "...",
                "input_tokens": 100,
                "output_tokens": 50,
                "operation": "reasoning"
            }
        }

        No fabricated token usage is created for
        deterministic analytical tools.
        """

        if not isinstance(
            observation,
            dict,
        ):
            return

        usage = observation.get(
            "_usage"
        )

        if not isinstance(
            usage,
            dict,
        ):
            return

        operation = usage.get(
            "operation"
        )

        if not isinstance(
            operation,
            str,
        ) or not operation.strip():
            operation = tool_name

        event = (
            self.cost_tracker.record_usage(
                model=usage[
                    "model"
                ],
                input_tokens=usage[
                    "input_tokens"
                ],
                output_tokens=usage[
                    "output_tokens"
                ],
                cached_input_tokens=int(
                    usage.get(
                        "cached_input_tokens",
                        0,
                    )
                ),
                operation=operation,
            )
        )

        state.add_cost(
            cost_usd=float(
                event[
                    "call_cost_usd"
                ]
            ),
            input_tokens=int(
                event[
                    "input_tokens"
                ]
            ),
            output_tokens=int(
                event[
                    "output_tokens"
                ]
            ),
        )

        self.audit_logger.log_event(
            task_id=state.task_id,
            event_type="cost",
            action=operation,
            status="recorded",
            details=event,
        )

    def _instrument_tool(
        self,
        tool_name: str,
        tool: ToolFunction,
    ) -> ToolFunction:
        """
        Add append-only audit and cost tracking
        around one AgentLoop-compatible tool.
        """

        def instrumented(
            state: AgentState,
        ) -> Any:

            self.audit_logger.log_event(
                task_id=state.task_id,
                event_type="tool_call",
                action=tool_name,
                status="started",
                details={
                    "turn_count":
                        state.turn_count,
                    "tool_call_count":
                        state.tool_call_count,
                },
            )

            try:
                observation = tool(
                    state
                )

                self._apply_usage(
                    state=state,
                    tool_name=tool_name,
                    observation=(
                        observation
                    ),
                )

            except Exception as exc:

                self.audit_logger.log_event(
                    task_id=(
                        state.task_id
                    ),
                    event_type=(
                        "tool_call"
                    ),
                    action=tool_name,
                    status="error",
                    details={
                        "error":
                            str(exc),
                    },
                )

                raise

            status = (
                self._observation_status(
                    observation
                )
            )

            self.audit_logger.log_event(
                task_id=state.task_id,
                event_type="tool_call",
                action=tool_name,
                status=status,
                details=(
                    self
                    ._observation_summary(
                        observation
                    )
                ),
            )

            return observation

        return instrumented

    def _build_tool_registry(
        self,
    ) -> dict[
        str,
        ToolFunction,
    ]:
        """
        Build the production tool registry.

        Every tool is protected by the AquaMind
        permission allowlist and instrumented.
        """

        base_tools: dict[
            str,
            ToolFunction,
        ] = {
            "validate_sensor_data":
                make_validate_sensor_data(
                    dataset_path=(
                        self.config
                        .dataset_path
                    ),
                    allowed_root=(
                        self.config
                        .allowed_data_root
                    ),
                ),
            "calculate_plant_kpis":
                make_calculate_plant_kpis(),
            "detect_anomalies":
                make_detect_anomalies(),
            "search_operational_knowledge":
                (
                    self
                    ._search_operational_knowledge
                ),
            "search_incident_memory":
                make_search_incident_memory(
                    self.memory,
                    limit=(
                        self.config
                        .knowledge_limit
                    ),
                ),
            "diagnose_issue":
                make_source_grounded_diagnosis(
                    base_tool=(
                        make_diagnose_issue()
                    ),
                    engine=(
                        self.diagnostic_engine
                    ),
                    vocabulary_path=(
                        self.evidence_vocabulary_path
                    ),
                    top_k=(
                        self.config
                        .diagnostic_top_k
                    ),
                ),
            "generate_incident_report":
                self._make_report_tool(),
        }

        protected_tools: dict[
            str,
            ToolFunction,
        ] = {}

        for (
            tool_name,
            base_tool,
        ) in base_tools.items():

            guarded = (
                make_permission_guard(
                    tool_name,
                    base_tool,
                )
            )

            protected_tools[
                tool_name
            ] = self._instrument_tool(
                tool_name,
                guarded,
            )

        return protected_tools

    def save_incident(
        self,
        state: AgentState,
        *,
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Persist a completed diagnosis.

        This is intentionally outside the autonomous
        planner because persistence is ASK_ON_WRITE.
        """

        base_tool = make_save_incident(
            self.memory,
            approved=approved,
        )

        guarded = make_permission_guard(
            "save_incident",
            base_tool,
            approved=approved,
        )

        instrumented = (
            self._instrument_tool(
                "save_incident",
                guarded,
            )
        )

        return instrumented(
            state
        )

    def _build_result(
        self,
        state: AgentState,
        safety: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the structured runtime result."""

        return {
            "state":
                state,
            "react_trace":
                list(
                    state.react_trace
                ),
            "report":
                self._latest_report(
                    state
                ),
            "safety_assessment":
                safety.get(
                    "assessment"
                ),
            "cost_summary":
                self.cost_tracker
                .summary(),
            "audit_integrity":
                self.audit_logger
                .verify_integrity(),
        }

    def run(
        self,
        *,
        task_id: str,
        user_request: str,
        plant_id: str = "demo-plant",
        diagnostic_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run one end-to-end AquaMind investigation.
        """

        state = AgentState(
            task_id=task_id,
            user_request=user_request,
            plant_id=plant_id,
            budget_cap_usd=(
                self.config
                .budget_cap_usd
            ),
            diagnostic_context=(
                dict(
                    diagnostic_context
                )
                if diagnostic_context
                is not None
                else {}
            ),
        )

        self.audit_logger.log_event(
            task_id=state.task_id,
            event_type="request",
            action="receive_request",
            status="received",
            details={
                "plant_id":
                    plant_id,
            },
        )

        safety = guard_agent_request(
            user_request
        )

        safety_status = (
            "allowed"
            if safety.get(
                "success"
            )
            else "blocked"
        )

        self.audit_logger.log_event(
            task_id=state.task_id,
            event_type="safety",
            action="inspect_request",
            status=safety_status,
            details={
                "assessment":
                    safety.get(
                        "assessment"
                    )
            },
        )

        if (
            safety.get(
                "success"
            )
            is not True
        ):
            message = str(
                safety.get(
                    "message",
                    (
                        "Request blocked by "
                        "AquaMind safety policy."
                    ),
                )
            )

            state.add_react_event(
                phase="observe",
                decision_summary=(
                    "Request-boundary safety inspection blocked "
                    "execution before any operational tool call."
                ),
                action="inspect_request",
                status="blocked",
                details={
                    "tool_call_count": 0,
                    "assessment": safety.get(
                        "assessment"
                    ),
                },
            )
            state.add_react_event(
                phase="terminate",
                decision_summary=message,
                action="inspect_request",
                status=(
                    TerminationReason
                    .SAFETY_BLOCK.value
                ),
            )

            state.terminate(
                reason=(
                    TerminationReason
                    .SAFETY_BLOCK
                ),
                final_answer=message,
            )

        else:
            state = self.agent_loop.run(
                state
            )

        self.audit_logger.log_event(
            task_id=state.task_id,
            event_type="termination",
            action="finish_task",
            status=state.status.value,
            details={
                "termination_reason": (
                    state
                    .termination_reason
                    .value
                    if state
                    .termination_reason
                    is not None
                    else None
                ),
                "turn_count":
                    state.turn_count,
                "tool_call_count":
                    state.tool_call_count,
                "cumulative_cost_usd":
                    (
                        state
                        .cumulative_cost_usd
                    ),
            },
        )

        return self._build_result(
            state,
            safety,
        )