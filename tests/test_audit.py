import json
from pathlib import Path

import pytest

from src.audit.logger import (
    GENESIS_HASH,
    AuditLogger,
    _canonical_json,
    _integrity_result,
    _record_hash,
    _utc_now,
)


def make_logger(
    tmp_path: Path,
) -> AuditLogger:
    return AuditLogger(
        tmp_path
        / "audit"
        / "events.jsonl"
    )


def log_sample(
    logger: AuditLogger,
    *,
    action: str = "detect_anomalies",
    status: str = "success",
):
    return logger.log_event(
        task_id="task-001",
        event_type="tool_call",
        action=action,
        status=status,
        details={
            "plant_id":
                "plant-a",
        },
        timestamp=(
            "2026-10-25T04:00:00Z"
        ),
        event_id="event-001",
    )


def test_utc_now_is_utc():
    value = _utc_now()

    assert value.endswith(
        "Z"
    )


def test_canonical_json_is_deterministic():
    first = _canonical_json(
        {
            "b": 2,
            "a": 1,
        }
    )

    second = _canonical_json(
        {
            "a": 1,
            "b": 2,
        }
    )

    assert first == second


def test_canonical_json_handles_non_json_object():
    value = _canonical_json(
        {
            "value":
                Path("example")
        }
    )

    assert (
        "example"
        in value
    )


def test_record_hash_is_deterministic():
    payload = {
        "a": 1,
        "b": 2,
    }

    assert (
        _record_hash(
            payload
        )
        == _record_hash(
            payload
        )
    )


def test_integrity_result():
    result = _integrity_result(
        valid=False,
        event_count=2,
        error="test",
        line_number=3,
    )

    assert result == {
        "valid": False,
        "event_count": 2,
        "error": "test",
        "line_number": 3,
    }


def test_logger_creates_parent_directory(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    assert (
        logger.log_path.parent.exists()
        is True
    )


def test_missing_log_uses_genesis_hash(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    assert (
        logger._last_hash()
        == GENESIS_HASH
    )


def test_empty_log_uses_genesis_hash(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.touch()

    assert (
        logger._last_hash()
        == GENESIS_HASH
    )


def test_blank_log_uses_genesis_hash(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        "\n\n",
        encoding="utf-8",
    )

    assert (
        logger._last_hash()
        == GENESIS_HASH
    )


def test_log_event_appends_record(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    result = log_sample(
        logger
    )

    assert (
        result["task_id"]
        == "task-001"
    )

    assert (
        result["previous_hash"]
        == GENESIS_HASH
    )

    assert (
        len(result["record_hash"])
        == 64
    )

    events = logger.read_events()

    assert len(
        events
    ) == 1


def test_default_timestamp_and_event_id(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    result = logger.log_event(
        task_id="task-default",
        event_type="agent",
        action="plan",
        status="success",
    )

    assert (
        len(result["event_id"])
        > 0
    )

    assert (
        result["timestamp"]
        .endswith("Z")
    )

    assert (
        result["details"]
        == {}
    )


def test_details_are_json_safe(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    result = logger.log_event(
        task_id="task-details",
        event_type="test",
        action="serialize",
        status="success",
        details={
            "path":
                Path("data.csv")
        },
    )

    assert (
        result["details"]["path"]
        == "data.csv"
    )


def test_multiple_events_form_hash_chain(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    first = logger.log_event(
        task_id="task-1",
        event_type="agent",
        action="plan",
        status="success",
        timestamp="2026-10-25T04:00:00Z",
        event_id="event-1",
    )

    second = logger.log_event(
        task_id="task-1",
        event_type="tool_call",
        action="validate_sensor_data",
        status="success",
        timestamp="2026-10-25T04:00:01Z",
        event_id="event-2",
    )

    assert (
        second["previous_hash"]
        == first["record_hash"]
    )


def test_hash_chain_survives_new_logger_instance(
    tmp_path: Path,
):
    log_path = (
        tmp_path
        / "audit.jsonl"
    )

    first_logger = AuditLogger(
        log_path
    )

    first = log_sample(
        first_logger
    )

    second_logger = AuditLogger(
        log_path
    )

    second = second_logger.log_event(
        task_id="task-002",
        event_type="agent",
        action="reflect",
        status="success",
        timestamp="2026-10-25T04:00:01Z",
        event_id="event-002",
    )

    assert (
        second["previous_hash"]
        == first["record_hash"]
    )


def test_task_id_is_required(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="task_id",
    ):
        logger.log_event(
            task_id=" ",
            event_type="agent",
            action="plan",
            status="success",
        )


def test_event_type_is_required(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="event_type",
    ):
        logger.log_event(
            task_id="task",
            event_type=" ",
            action="plan",
            status="success",
        )


def test_action_is_required(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="action",
    ):
        logger.log_event(
            task_id="task",
            event_type="agent",
            action=" ",
            status="success",
        )


def test_status_is_required(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="status",
    ):
        logger.log_event(
            task_id="task",
            event_type="agent",
            action="plan",
            status=" ",
        )


def test_read_missing_log_returns_empty(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    assert (
        logger.read_events()
        == []
    )


def test_read_events_skips_blank_lines(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    log_sample(
        logger
    )

    with logger.log_path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "\n"
        )

    events = logger.read_events()

    assert len(
        events
    ) == 1


def test_verify_missing_log_is_valid(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is True
    assert result["event_count"] == 0


def test_verify_valid_log(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    log_sample(
        logger
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is True
    assert result["event_count"] == 1
    assert result["error"] is None


def test_verify_skips_blank_lines(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        "\n",
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is True
    assert result["event_count"] == 0


def test_verify_detects_malformed_json(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        "{not-json}\n",
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is False

    assert (
        result["error"]
        == "Malformed JSON audit record."
    )

    assert (
        result["line_number"]
        == 1
    )


def test_verify_rejects_non_object_record(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        '["invalid"]\n',
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is False

    assert (
        result["error"]
        == (
            "Audit record must be "
            "a JSON object."
        )
    )


def test_verify_detects_missing_record_hash(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        '{"previous_hash":"'
        + GENESIS_HASH
        + '"}\n',
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is False

    assert (
        "record_hash"
        in result["error"]
    )


def test_verify_detects_broken_chain(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    record = log_sample(
        logger
    )

    record[
        "previous_hash"
    ] = "1" * 64

    logger.log_path.write_text(
        _canonical_json(
            record
        )
        + "\n",
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is False

    assert (
        result["error"]
        == "Audit hash chain is broken."
    )


def test_verify_detects_modified_content(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    record = log_sample(
        logger
    )

    record["status"] = "tampered"

    logger.log_path.write_text(
        _canonical_json(
            record
        )
        + "\n",
        encoding="utf-8",
    )

    result = (
        logger.verify_integrity()
    )

    assert result["valid"] is False

    assert (
        result["error"]
        == (
            "Audit record contents "
            "have been modified."
        )
    )


def test_last_hash_rejects_invalid_json(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        "{bad-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        logger._last_hash()


def test_last_hash_rejects_missing_hash(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    logger.log_path.write_text(
        '{"event":"test"}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="record_hash",
    ):
        logger._last_hash()


def test_last_hash_ignores_blank_trailing_line(
    tmp_path: Path,
):
    logger = make_logger(
        tmp_path
    )

    record = log_sample(
        logger
    )

    with logger.log_path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "\n"
        )

    assert (
        logger._last_hash()
        == record["record_hash"]
    )