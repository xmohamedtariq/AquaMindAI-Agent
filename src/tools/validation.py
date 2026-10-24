from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.agent.state import AgentState
from src.tools.data_loader import load_operational_data


NUMERIC_SENSOR_COLUMNS = {
    "feed_pressure",
    "concentrate_pressure",
    "permeate_pressure",
    "feed_flow",
    "permeate_flow",
    "concentrate_flow",
    "feed_tds",
    "permeate_tds",
    "feed_conductivity",
    "permeate_conductivity",
    "temperature",
    "recovery_rate",
    "differential_pressure",
    "energy_consumption",
    "specific_energy_consumption",
}


def _normalise_column_name(
    column: str,
) -> str:
    """
    Convert a column name into a consistent
    machine-friendly format.
    """

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def _normalise_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return a copy with normalized column names."""

    result = dataframe.copy()

    result.columns = [
        _normalise_column_name(column)
        for column in result.columns
    ]

    return result


def _records_from_dataframe(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Convert a DataFrame into JSON-safe records."""

    clean = dataframe.astype(
        object
    ).where(
        pd.notna(dataframe),
        None,
    )

    return clean.to_dict(
        orient="records"
    )


def validate_sensor_records(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate desalination operational records.

    Performs:
    - schema normalization
    - timestamp validation
    - duplicate recovery
    - numeric coercion
    - missing-value assessment
    - chronological ordering
    - data-quality scoring

    This function validates data quality only.
    It does not perform engineering diagnosis.
    """

    if not records:
        return {
            "success": False,
            "recoverable": False,
            "error": "No sensor records were provided.",
        }

    dataframe = pd.DataFrame(
        records
    )

    dataframe = _normalise_columns(
        dataframe
    )

    # ---------------------------------------------------------
    # Required timestamp
    # ---------------------------------------------------------

    if "timestamp" not in dataframe.columns:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Required column 'timestamp' "
                "is missing."
            ),
        }

    # ---------------------------------------------------------
    # Supported operational columns
    # ---------------------------------------------------------

    available_numeric_columns = [
        column
        for column in dataframe.columns
        if column in NUMERIC_SENSOR_COLUMNS
    ]

    if not available_numeric_columns:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "No supported operational sensor "
                "columns were found."
            ),
        }

    original_rows = len(
        dataframe
    )

    issues: list[str] = []
    recovery_actions: list[str] = []

    # ---------------------------------------------------------
    # Timestamp validation
    # ---------------------------------------------------------

    parsed_timestamps = pd.to_datetime(
        dataframe["timestamp"],
        errors="coerce",
        utc=True,
        format="mixed",
    )

    invalid_timestamp_mask = (
        parsed_timestamps.isna()
    )

    invalid_timestamp_count = int(
        invalid_timestamp_mask.sum()
    )

    if invalid_timestamp_count > 0:
        issues.append(
            (
                f"{invalid_timestamp_count} row(s) "
                "contained invalid timestamps."
            )
        )

        dataframe = dataframe.loc[
            ~invalid_timestamp_mask
        ].copy()

        parsed_timestamps = (
            parsed_timestamps.loc[
                ~invalid_timestamp_mask
            ]
        )

        recovery_actions.append(
            "Removed rows with invalid timestamps."
        )

    if dataframe.empty:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "No valid rows remain after "
                "timestamp validation."
            ),
        }

    dataframe["timestamp"] = (
        parsed_timestamps
        .dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    # ---------------------------------------------------------
    # Duplicate timestamp recovery
    # ---------------------------------------------------------

    duplicate_count = int(
        dataframe.duplicated(
            subset=["timestamp"],
            keep="last",
        ).sum()
    )

    if duplicate_count > 0:
        issues.append(
            (
                f"{duplicate_count} duplicate "
                "timestamp row(s) were detected."
            )
        )

        dataframe = dataframe.drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )

        recovery_actions.append(
            (
                "Removed duplicate timestamps "
                "and kept the latest row."
            )
        )

    # ---------------------------------------------------------
    # Numeric coercion
    # ---------------------------------------------------------

    coercion_failures: dict[str, int] = {}

    for column in available_numeric_columns:
        before_missing = int(
            dataframe[column]
            .isna()
            .sum()
        )

        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        after_missing = int(
            dataframe[column]
            .isna()
            .sum()
        )

        introduced_missing = (
            after_missing
            - before_missing
        )

        if introduced_missing > 0:
            coercion_failures[
                column
            ] = introduced_missing

    if coercion_failures:
        total_failures = sum(
            coercion_failures.values()
        )

        issues.append(
            (
                f"{total_failures} non-numeric "
                "sensor value(s) were converted "
                "to missing values."
            )
        )

        recovery_actions.append(
            (
                "Converted invalid numeric sensor "
                "values to missing values."
            )
        )

    # ---------------------------------------------------------
    # Missing-value assessment
    # ---------------------------------------------------------

    missing_values = {
        column: int(
            dataframe[column]
            .isna()
            .sum()
        )
        for column in available_numeric_columns
        if dataframe[column]
        .isna()
        .any()
    }

    if missing_values:
        issues.append(
            "Missing sensor values are present."
        )

    # ---------------------------------------------------------
    # Chronological ordering
    # ---------------------------------------------------------

    dataframe = dataframe.sort_values(
        by="timestamp"
    ).reset_index(
        drop=True
    )

    clean_rows = len(
        dataframe
    )

    removed_rows = (
        original_rows
        - clean_rows
    )

    recovered = bool(
        recovery_actions
    )

    # ---------------------------------------------------------
    # Quality score
    # ---------------------------------------------------------
    #
    # At this point:
    # - at least one valid row exists
    # - at least one supported numeric column exists
    #
    # Therefore total_numeric_cells is always > 0.
    # ---------------------------------------------------------

    total_numeric_cells = (
        clean_rows
        * len(available_numeric_columns)
    )

    missing_numeric_cells = sum(
        missing_values.values()
    )

    completeness = (
        1.0
        - (
            missing_numeric_cells
            / total_numeric_cells
        )
    )

    row_retention = (
        clean_rows
        / original_rows
    )

    quality_score = round(
        max(
            0.0,
            min(
                100.0,
                (
                    completeness
                    * 70.0
                    + row_retention
                    * 30.0
                ),
            ),
        ),
        2,
    )

    return {
        "success": True,
        "recoverable": False,
        "recovered": recovered,
        "original_row_count": original_rows,
        "clean_row_count": clean_rows,
        "removed_row_count": removed_rows,
        "invalid_timestamp_count": (
            invalid_timestamp_count
        ),
        "duplicate_timestamp_count": (
            duplicate_count
        ),
        "coercion_failures": (
            coercion_failures
        ),
        "missing_values": missing_values,
        "operational_columns": (
            available_numeric_columns
        ),
        "issues": issues,
        "recovery_actions": (
            recovery_actions
        ),
        "quality_score": quality_score,
        "records": (
            _records_from_dataframe(
                dataframe
            )
        ),
    }


def make_validate_sensor_data(
    dataset_path: str | Path,
    allowed_root: str | Path = "data",
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """
    Create an AgentLoop-compatible validation tool.

    Secure loader -> validation -> recovery.
    """

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        loaded = load_operational_data(
            state=state,
            dataset_path=dataset_path,
            allowed_root=allowed_root,
        )

        if loaded["success"] is False:
            return loaded

        result = validate_sensor_records(
            loaded["records"]
        )

        if result["success"]:
            result["dataset_name"] = (
                loaded["dataset_name"]
            )

        return result

    return tool