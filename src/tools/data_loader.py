from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from src.agent.state import AgentState


DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _failure(
    message: str,
) -> dict[str, Any]:
    """Return a standard non-recoverable loading failure."""

    return {
        "success": False,
        "recoverable": False,
        "error": message,
    }


def _resolve_under_root(
    dataset_path: str | Path,
    allowed_root: str | Path,
) -> Path:
    """
    Resolve a dataset path and ensure that it remains
    inside the approved data directory.
    """

    root = Path(
        allowed_root
    ).resolve()

    candidate = Path(
        dataset_path
    )

    if not candidate.is_absolute():
        candidate = (
            root / candidate
        ).resolve()

    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(
            root
        )

    except ValueError as exc:
        raise ValueError(
            "Dataset path is outside the approved data directory."
        ) from exc

    return candidate


def _normalise_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert a DataFrame into JSON-friendly records.

    Missing values are converted to None.
    """

    clean = dataframe.astype(
        object
    ).where(
        pd.notna(dataframe),
        None,
    )

    return clean.to_dict(
        orient="records"
    )


def load_operational_data(
    state: AgentState,
    dataset_path: str | Path,
    allowed_root: str | Path = "data",
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> dict[str, Any]:
    """
    Safely load a CSV desalination operational dataset.

    Security controls:
    - CSV files only
    - approved directory only
    - file-size limit
    - no arbitrary code execution
    """

    del state

    try:
        path = _resolve_under_root(
            dataset_path=dataset_path,
            allowed_root=allowed_root,
        )

    except ValueError as exc:
        return _failure(
            str(exc)
        )

    if path.suffix.lower() != ".csv":
        return _failure(
            "Unsupported dataset type. Only CSV files are allowed."
        )

    if not path.exists():
        return _failure(
            "Dataset file does not exist."
        )

    if not path.is_file():
        return _failure(
            "Dataset path does not point to a file."
        )

    if (
        path.stat().st_size
        > max_file_size_bytes
    ):
        return _failure(
            "Dataset exceeds the configured file-size limit."
        )

    try:
        dataframe = pd.read_csv(
            path
        )

    except (
        EmptyDataError,
        ParserError,
        UnicodeDecodeError,
        OSError,
    ) as exc:
        return _failure(
            f"Unable to read dataset: {exc}"
        )

    if dataframe.empty:
        return _failure(
            "Dataset contains no operational rows."
        )

    records = _normalise_records(
        dataframe
    )

    return {
        "success": True,
        "recoverable": False,
        "dataset_name": path.name,
        "row_count": int(
            len(dataframe)
        ),
        "column_count": int(
            len(dataframe.columns)
        ),
        "columns": [
            str(column)
            for column in dataframe.columns
        ],
        "records": records,
    }


def make_load_operational_data(
    dataset_path: str | Path,
    allowed_root: str | Path = "data",
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> Callable[[AgentState], dict[str, Any]]:
    """
    Build an AgentLoop-compatible data-loading tool.
    """

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return load_operational_data(
            state=state,
            dataset_path=dataset_path,
            allowed_root=allowed_root,
            max_file_size_bytes=max_file_size_bytes,
        )

    return tool