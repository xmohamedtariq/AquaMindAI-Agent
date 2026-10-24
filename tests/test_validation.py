from pathlib import Path

import pandas as pd

from src.agent.state import AgentState
from src.tools.validation import (
    _normalise_column_name,
    _normalise_columns,
    _records_from_dataframe,
    make_validate_sensor_data,
    validate_sensor_records,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="validation-test",
        user_request=(
            "Validate desalination plant data"
        ),
    )


def test_normalise_column_name():
    assert (
        _normalise_column_name(
            " Feed Pressure "
        )
        == "feed_pressure"
    )

    assert (
        _normalise_column_name(
            "Permeate-Flow"
        )
        == "permeate_flow"
    )


def test_normalise_columns():
    dataframe = pd.DataFrame(
        {
            " Feed Pressure ": [60],
            "Permeate-Flow": [120],
        }
    )

    result = _normalise_columns(
        dataframe
    )

    assert list(
        result.columns
    ) == [
        "feed_pressure",
        "permeate_flow",
    ]


def test_records_from_dataframe():
    dataframe = pd.DataFrame(
        {
            "pressure": [
                60.0,
                None,
            ],
        }
    )

    result = _records_from_dataframe(
        dataframe
    )

    assert result == [
        {
            "pressure": 60.0,
        },
        {
            "pressure": None,
        },
    ]


def test_empty_records_fail():
    result = validate_sensor_records(
        []
    )

    assert result["success"] is False
    assert result["recoverable"] is False

    assert (
        result["error"]
        == "No sensor records were provided."
    )


def test_missing_timestamp_fails():
    result = validate_sensor_records(
        [
            {
                "feed_pressure": 60,
            }
        ]
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Required column 'timestamp' "
            "is missing."
        )
    )


def test_no_supported_sensor_columns_fails():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "unknown_sensor": 123,
            }
        ]
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "No supported operational sensor "
            "columns were found."
        )
    )


def test_valid_dataset_passes():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": 60.0,
                "permeate_flow": 120.0,
            },
            {
                "timestamp":
                    "2026-10-24T10:05:00",
                "feed_pressure": 61.0,
                "permeate_flow": 118.0,
            },
        ]
    )

    assert result["success"] is True
    assert result["recovered"] is False

    assert result["original_row_count"] == 2
    assert result["clean_row_count"] == 2
    assert result["removed_row_count"] == 0

    assert result["quality_score"] == 100.0

    assert (
        result["recovery_actions"]
        == []
    )


def test_invalid_timestamp_is_removed():
    result = validate_sensor_records(
        [
            {
                "timestamp": "invalid-date",
                "feed_pressure": 60,
            },
            {
                "timestamp":
                    "2026-10-24T10:05:00",
                "feed_pressure": 61,
            },
        ]
    )

    assert result["success"] is True
    assert result["recovered"] is True

    assert (
        result["invalid_timestamp_count"]
        == 1
    )

    assert result["clean_row_count"] == 1
    assert result["removed_row_count"] == 1


def test_all_invalid_timestamps_fail():
    result = validate_sensor_records(
        [
            {
                "timestamp": "bad",
                "feed_pressure": 60,
            },
            {
                "timestamp": "also-bad",
                "feed_pressure": 61,
            },
        ]
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "No valid rows remain after "
            "timestamp validation."
        )
    )


def test_duplicate_timestamps_are_recovered():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": 60,
            },
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": 62,
            },
        ]
    )

    assert result["success"] is True
    assert result["recovered"] is True

    assert (
        result["duplicate_timestamp_count"]
        == 1
    )

    assert result["clean_row_count"] == 1

    assert (
        result["records"][0]
        ["feed_pressure"]
        == 62
    )


def test_non_numeric_value_is_recovered():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": "bad-value",
            },
            {
                "timestamp":
                    "2026-10-24T10:05:00",
                "feed_pressure": "61.5",
            },
        ]
    )

    assert result["success"] is True
    assert result["recovered"] is True

    assert result[
        "coercion_failures"
    ] == {
        "feed_pressure": 1,
    }

    assert result[
        "missing_values"
    ] == {
        "feed_pressure": 1,
    }

    assert (
        result["records"][0]
        ["feed_pressure"]
        is None
    )


def test_existing_missing_value_is_reported():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": None,
            },
            {
                "timestamp":
                    "2026-10-24T10:05:00",
                "feed_pressure": 61,
            },
        ]
    )

    assert result["success"] is True

    assert result[
        "missing_values"
    ] == {
        "feed_pressure": 1,
    }

    assert (
        "Missing sensor values are present."
        in result["issues"]
    )


def test_rows_are_sorted_by_timestamp():
    result = validate_sensor_records(
        [
            {
                "timestamp":
                    "2026-10-24T10:05:00",
                "feed_pressure": 61,
            },
            {
                "timestamp":
                    "2026-10-24T10:00:00",
                "feed_pressure": 60,
            },
        ]
    )

    assert result["success"] is True

    assert (
        result["records"][0]
        ["feed_pressure"]
        == 60
    )

    assert (
        result["records"][1]
        ["feed_pressure"]
        == 61
    )


def test_column_names_are_normalised_before_validation():
    result = validate_sensor_records(
        [
            {
                " Timestamp ":
                    "2026-10-24T10:00:00",
                "Feed Pressure": 60,
            }
        ]
    )

    assert result["success"] is True

    assert (
        result["operational_columns"]
        == ["feed_pressure"]
    )


def test_factory_loads_and_validates_csv(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "plant.csv"
    )

    dataset.write_text(
        (
            "timestamp,feed_pressure\n"
            "2026-10-24T10:00:00,60\n"
        ),
        encoding="utf-8",
    )

    tool = make_validate_sensor_data(
        dataset_path="plant.csv",
        allowed_root=tmp_path,
    )

    result = tool(
        make_state()
    )

    assert result["success"] is True

    assert (
        result["dataset_name"]
        == "plant.csv"
    )


def test_factory_returns_loader_failure(
    tmp_path: Path,
):
    tool = make_validate_sensor_data(
        dataset_path="missing.csv",
        allowed_root=tmp_path,
    )

    result = tool(
        make_state()
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "Dataset file does not exist."
    )


def test_factory_returns_validation_failure_after_load(
    tmp_path: Path,
):
    """
    Cover the case where loading succeeds,
    but validation rejects the dataset.
    """

    dataset = (
        tmp_path / "invalid-schema.csv"
    )

    dataset.write_text(
        (
            "timestamp,unknown_sensor\n"
            "2026-10-24T10:00:00,123\n"
        ),
        encoding="utf-8",
    )

    tool = make_validate_sensor_data(
        dataset_path="invalid-schema.csv",
        allowed_root=tmp_path,
    )

    result = tool(
        make_state()
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "No supported operational sensor "
            "columns were found."
        )
    )

    assert (
        "dataset_name"
        not in result
    )