import re
from dataclasses import dataclass
from typing import Any


PROMPT_INJECTION_PATTERNS = (
    (
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget|override)\b"
            r".{0,50}"
            r"\b(previous|prior|system|developer|safety|"
            r"instructions?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "hidden_prompt_extraction",
        re.compile(
            r"\b(reveal|show|print|expose|display)\b"
            r".{0,50}"
            r"\b(system prompt|developer message|"
            r"hidden instructions?|internal instructions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "safety_bypass",
        re.compile(
            r"\b(bypass|disable|remove|circumvent|override)\b"
            r".{0,50}"
            r"\b(safety|permission|permissions|guardrail|"
            r"guardrails|approval|authorization)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "forced_tool_execution",
        re.compile(
            r"\b(call|execute|run|use)\b"
            r".{0,50}"
            r"\b(tool|function|command)\b"
            r".{0,50}"
            r"\b(without|despite|ignore|bypass)\b",
            re.IGNORECASE,
        ),
    ),
)


PHYSICAL_CONTROL_PATTERNS = (
    (
        "valve_control",
        re.compile(
            r"\b(open|close|adjust|operate)\b"
            r".{0,40}"
            r"\b(valve|valves)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pump_control",
        re.compile(
            r"\b(start|stop|restart|activate|deactivate)\b"
            r".{0,40}"
            r"\b(pump|pumps)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "setpoint_change",
        re.compile(
            r"\b(change|set|adjust|modify)\b"
            r".{0,40}"
            r"\b(setpoint|set-point|set point)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "plant_shutdown",
        re.compile(
            r"\b(stop|shutdown|shut down|restart)\b"
            r".{0,40}"
            r"\b(plant|system|desalination plant)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "cleaning_cycle_control",
        re.compile(
            r"\b(start|stop|trigger|initiate)\b"
            r".{0,40}"
            r"\b(cleaning cycle|cip cycle|cip)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class SafetyAssessment:
    """Structured AquaMind request-boundary assessment."""

    safe: bool
    source: str
    prompt_injection_detected: bool
    physical_control_detected: bool
    indicators: tuple[str, ...]
    reason: str

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return a serializable safety assessment."""

        return {
            "safe": self.safe,
            "source": self.source,
            "prompt_injection_detected":
                self.prompt_injection_detected,
            "physical_control_detected":
                self.physical_control_detected,
            "indicators": list(
                self.indicators
            ),
            "reason": self.reason,
        }


def normalize_text(
    text: str,
) -> str:
    """Normalize whitespace while preserving content."""

    return " ".join(
        text.split()
    )


def _matched_indicators(
    text: str,
    patterns: tuple[
        tuple[
            str,
            re.Pattern[str],
        ],
        ...,
    ],
) -> tuple[str, ...]:
    """Return labels for all matching safety patterns."""

    matches: list[str] = []

    for label, pattern in patterns:
        if pattern.search(
            text
        ):
            matches.append(
                label
            )

    return tuple(
        matches
    )


def inspect_input(
    text: str,
    *,
    source: str = "user",
) -> SafetyAssessment:
    """
    Inspect untrusted content before agent execution.

    AquaMind is permitted to analyze and recommend,
    but it does not perform direct physical control.
    """

    normalized = normalize_text(
        text
    )

    injection_indicators = (
        _matched_indicators(
            normalized,
            PROMPT_INJECTION_PATTERNS,
        )
    )

    physical_indicators = (
        _matched_indicators(
            normalized,
            PHYSICAL_CONTROL_PATTERNS,
        )
    )

    injection_detected = bool(
        injection_indicators
    )

    physical_detected = bool(
        physical_indicators
    )

    indicators = (
        injection_indicators
        + physical_indicators
    )

    if (
        injection_detected
        and physical_detected
    ):
        reason = (
            "Request contains prompt-injection "
            "indicators and attempts to request "
            "physical plant control."
        )

    elif injection_detected:
        reason = (
            "Request contains prompt-injection "
            "or safety-bypass indicators."
        )

    elif physical_detected:
        reason = (
            "Request attempts physical plant control. "
            "AquaMind is restricted to analysis, "
            "investigation, and recommendations."
        )

    else:
        reason = (
            "No prompt-injection or prohibited "
            "physical-control indicators detected."
        )

    return SafetyAssessment(
        safe=not (
            injection_detected
            or physical_detected
        ),
        source=source,
        prompt_injection_detected=(
            injection_detected
        ),
        physical_control_detected=(
            physical_detected
        ),
        indicators=indicators,
        reason=reason,
    )


def guard_agent_request(
    text: str,
    *,
    source: str = "user",
) -> dict[str, Any]:
    """
    Enforce AquaMind's request boundary.

    Unsafe requests emit the `_safety_violation`
    signal understood by the agent loop.
    """

    assessment = inspect_input(
        text,
        source=source,
    )

    if assessment.safe:
        return {
            "success": True,
            "recoverable": False,
            "assessment":
                assessment.to_dict(),
        }

    return {
        "success": False,
        "recoverable": False,
        "_safety_violation": True,
        "assessment":
            assessment.to_dict(),
        "message":
            assessment.reason,
    }