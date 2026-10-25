from src.safety.permissions import (
    PermissionLevel,
    evaluate_permission,
    get_permission_level,
    make_permission_guard,
    normalize_tool_name,
)


def test_normalize_tool_name():
    assert (
        normalize_tool_name(
            "  DETECT_ANOMALIES  "
        )
        == "detect_anomalies"
    )


def test_auto_tool_level():
    assert (
        get_permission_level(
            "detect_anomalies"
        )
        == PermissionLevel.AUTO
    )


def test_write_tool_level():
    assert (
        get_permission_level(
            "save_incident"
        )
        == PermissionLevel.ASK_ON_WRITE
    )


def test_high_impact_tool_level():
    assert (
        get_permission_level(
            "control_valve"
        )
        == PermissionLevel.ALWAYS_ASK
    )


def test_unknown_tool_has_no_level():
    assert (
        get_permission_level(
            "delete_everything"
        )
        is None
    )


def test_empty_tool_is_denied():
    result = evaluate_permission(
        "   "
    )

    assert (
        result.recognized
        is False
    )

    assert (
        result.allowed
        is False
    )

    assert (
        result.requires_approval
        is False
    )

    assert (
        result.permission_level
        is None
    )


def test_unknown_tool_is_default_denied():
    result = evaluate_permission(
        "unknown_tool"
    )

    assert (
        result.recognized
        is False
    )

    assert (
        result.allowed
        is False
    )

    assert (
        "allowlist"
        in result.reason
    )


def test_auto_tool_is_allowed():
    result = evaluate_permission(
        "calculate_plant_kpis"
    )

    assert (
        result.recognized
        is True
    )

    assert (
        result.allowed
        is True
    )

    assert (
        result.requires_approval
        is False
    )

    assert (
        result.permission_level
        == PermissionLevel.AUTO
    )


def test_write_tool_requires_approval():
    result = evaluate_permission(
        "save_incident"
    )

    assert (
        result.recognized
        is True
    )

    assert (
        result.allowed
        is False
    )

    assert (
        result.requires_approval
        is True
    )

    assert (
        result.permission_level
        == PermissionLevel.ASK_ON_WRITE
    )

    assert (
        "Persistent write"
        in result.reason
    )


def test_write_tool_executes_after_approval():
    result = evaluate_permission(
        "save_incident",
        approved=True,
    )

    assert (
        result.allowed
        is True
    )

    assert (
        result.requires_approval
        is False
    )

    assert (
        result.permission_level
        == PermissionLevel.ASK_ON_WRITE
    )


def test_always_ask_requires_approval():
    result = evaluate_permission(
        "control_valve"
    )

    assert (
        result.allowed
        is False
    )

    assert (
        result.requires_approval
        is True
    )

    assert (
        result.permission_level
        == PermissionLevel.ALWAYS_ASK
    )

    assert (
        "every"
        in result.reason
    )


def test_always_ask_allows_single_approved_execution():
    result = evaluate_permission(
        "control_valve",
        approved=True,
    )

    assert (
        result.allowed
        is True
    )

    assert (
        result.requires_approval
        is False
    )

    assert (
        result.permission_level
        == PermissionLevel.ALWAYS_ASK
    )


def test_permission_decision_serialization():
    result = evaluate_permission(
        "save_incident"
    )

    serialized = (
        result.to_dict()
    )

    assert (
        serialized[
            "tool_name"
        ]
        == "save_incident"
    )

    assert (
        serialized[
            "permission_level"
        ]
        == "ASK_ON_WRITE"
    )


def test_unrecognized_decision_serialization():
    result = evaluate_permission(
        "not_allowed"
    )

    serialized = (
        result.to_dict()
    )

    assert (
        serialized[
            "permission_level"
        ]
        is None
    )


def test_auto_guard_executes_tool():
    calls = []

    def tool(state):
        calls.append(
            state
        )

        return {
            "success": True,
            "value": 42,
        }

    guarded = make_permission_guard(
        "detect_anomalies",
        tool,
    )

    state = object()

    result = guarded(
        state
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result["value"]
        == 42
    )

    assert calls == [
        state
    ]


def test_write_guard_blocks_without_approval():
    calls = []

    def tool(state):
        calls.append(
            state
        )

        return {
            "success": True,
        }

    guarded = make_permission_guard(
        "save_incident",
        tool,
    )

    result = guarded(
        object()
    )

    assert (
        result["success"]
        is False
    )

    assert (
        result[
            "_permission_required"
        ]
        is True
    )

    assert (
        result[
            "permission_level"
        ]
        == "ASK_ON_WRITE"
    )

    assert calls == []


def test_write_guard_executes_with_approval():
    calls = []

    def tool(state):
        calls.append(
            state
        )

        return {
            "success": True,
            "saved": True,
        }

    guarded = make_permission_guard(
        "save_incident",
        tool,
        approved=True,
    )

    state = object()

    result = guarded(
        state
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result["saved"]
        is True
    )

    assert calls == [
        state
    ]


def test_always_ask_guard_blocks_without_approval():
    guarded = make_permission_guard(
        "control_valve",
        lambda state: {
            "success": True,
        },
    )

    result = guarded(
        object()
    )

    assert (
        result["success"]
        is False
    )

    assert (
        result[
            "_permission_required"
        ]
        is True
    )

    assert (
        result[
            "permission_level"
        ]
        == "ALWAYS_ASK"
    )


def test_unknown_guard_becomes_safety_violation():
    calls = []

    def tool(state):
        calls.append(
            state
        )

        return {
            "success": True,
        }

    guarded = make_permission_guard(
        "malicious_unknown_tool",
        tool,
    )

    result = guarded(
        object()
    )

    assert (
        result["success"]
        is False
    )

    assert (
        result[
            "_safety_violation"
        ]
        is True
    )

    assert (
        result[
            "permission"
        ][
            "recognized"
        ]
        is False
    )

    assert calls == []