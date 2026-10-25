from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PermissionLevel(str, Enum):
    """
    AquaMind permission levels.

    AUTO:
        Safe read-only or analytical operation.

    ASK_ON_WRITE:
        Persistent write/export operation that requires
        explicit human approval before execution.

    ALWAYS_ASK:
        High-impact operation that requires explicit
        human approval for every execution attempt.
    """

    AUTO = "AUTO"
    ASK_ON_WRITE = "ASK_ON_WRITE"
    ALWAYS_ASK = "ALWAYS_ASK"


AUTO_TOOLS = frozenset(
    {
        "load_operational_data",
        "validate_sensor_data",
        "calculate_plant_kpis",
        "detect_anomalies",
        "diagnose_issue",
        "search_operational_knowledge",
        "search_incident_memory",
    }
)


ASK_ON_WRITE_TOOLS = frozenset(
    {
        "save_incident",
        "generate_incident_report",
    }
)


# These high-impact operations are intentionally NOT part
# of the AquaMind MVP execution tool registry.
#
# They are defined only so the permission system has an
# explicit security policy if such operations are ever
# requested.
ALWAYS_ASK_TOOLS = frozenset(
    {
        "control_valve",
        "control_pump",
        "change_setpoint",
        "start_cleaning_cycle",
        "stop_plant",
    }
)


@dataclass(frozen=True)
class PermissionDecision:
    """Structured result of a permission evaluation."""

    tool_name: str
    recognized: bool
    allowed: bool
    requires_approval: bool
    permission_level: PermissionLevel | None
    reason: str

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return a serializable permission decision."""

        return {
            "tool_name": self.tool_name,
            "recognized": self.recognized,
            "allowed": self.allowed,
            "requires_approval":
                self.requires_approval,
            "permission_level": (
                self.permission_level.value
                if self.permission_level
                is not None
                else None
            ),
            "reason": self.reason,
        }


def normalize_tool_name(
    tool_name: str,
) -> str:
    """Normalize a tool name before policy evaluation."""

    return tool_name.strip().lower()


def get_permission_level(
    tool_name: str,
) -> PermissionLevel | None:
    """
    Return the configured permission level.

    Unknown tools return None and are denied by default.
    """

    normalized = normalize_tool_name(
        tool_name
    )

    if normalized in AUTO_TOOLS:
        return PermissionLevel.AUTO

    if normalized in ASK_ON_WRITE_TOOLS:
        return PermissionLevel.ASK_ON_WRITE

    if normalized in ALWAYS_ASK_TOOLS:
        return PermissionLevel.ALWAYS_ASK

    return None


def evaluate_permission(
    tool_name: str,
    *,
    approved: bool = False,
) -> PermissionDecision:
    """
    Evaluate whether a tool may execute.

    Security model:
    - Explicit allowlist.
    - Unknown tools are denied by default.
    - AUTO tools execute without approval.
    - ASK_ON_WRITE requires explicit approval.
    - ALWAYS_ASK requires explicit approval for every
      execution attempt.
    """

    normalized = normalize_tool_name(
        tool_name
    )

    if not normalized:
        return PermissionDecision(
            tool_name=normalized,
            recognized=False,
            allowed=False,
            requires_approval=False,
            permission_level=None,
            reason=(
                "Empty tool names are not permitted."
            ),
        )

    level = get_permission_level(
        normalized
    )

    if level is None:
        return PermissionDecision(
            tool_name=normalized,
            recognized=False,
            allowed=False,
            requires_approval=False,
            permission_level=None,
            reason=(
                "Tool is not present in the "
                "AquaMind permission allowlist."
            ),
        )

    if level == PermissionLevel.AUTO:
        return PermissionDecision(
            tool_name=normalized,
            recognized=True,
            allowed=True,
            requires_approval=False,
            permission_level=level,
            reason=(
                "Read-only or analytical tool "
                "is authorized automatically."
            ),
        )

    if approved:
        return PermissionDecision(
            tool_name=normalized,
            recognized=True,
            allowed=True,
            requires_approval=False,
            permission_level=level,
            reason=(
                "Explicit human approval was "
                "provided for this execution."
            ),
        )

    if level == PermissionLevel.ALWAYS_ASK:
        reason = (
            "High-impact operation requires "
            "explicit human approval for every "
            "execution attempt."
        )
    else:
        reason = (
            "Persistent write operation requires "
            "explicit human approval."
        )

    return PermissionDecision(
        tool_name=normalized,
        recognized=True,
        allowed=False,
        requires_approval=True,
        permission_level=level,
        reason=reason,
    )


def make_permission_guard(
    tool_name: str,
    tool: Callable[[Any], Any],
    *,
    approved: bool = False,
) -> Callable[[Any], Any]:
    """
    Wrap an AgentLoop-compatible tool with permission
    enforcement.

    Unknown tools become safety violations.

    Approval-gated tools return the structured signals
    already understood by the AquaMind agent loop.
    """

    def guarded_tool(
        state: Any,
    ) -> Any:

        decision = evaluate_permission(
            tool_name,
            approved=approved,
        )

        if not decision.recognized:
            return {
                "success": False,
                "recoverable": False,
                "_safety_violation": True,
                "permission":
                    decision.to_dict(),
                "message":
                    decision.reason,
            }

        if not decision.allowed:
            return {
                "success": False,
                "recoverable": False,
                "_permission_required": True,
                "permission_level": (
                    decision
                    .permission_level
                    .value
                ),
                "permission":
                    decision.to_dict(),
                "message":
                    decision.reason,
            }

        return tool(
            state
        )

    return guarded_tool