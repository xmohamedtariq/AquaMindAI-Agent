from pathlib import Path

from src.agent.state import AgentState
from src.tools.data_loader import (
    _normalise_records,
    _resolve_under_root,
    load_operational_data,
    make_load_operational_data,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="data-loader-test",
        user_request="Load plant operational data",
    )


def test_resolve_relative_path_inside_root(
    tmp_path: Path,
):
    result = _resolve_under_root(
        dataset_path="plant.csv",
        allowed_root=tmp_path,
    )

    assert result == (
        tmp_path / "plant.csv"
    ).resolve()


def test_resolve_absolute_path_inside_root(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "plant.csv"
    ).resolve()

    result = _resolve_under_root(
        dataset_path=dataset,
        allowed_root=tmp_path,
    )

    assert result == dataset


def test_path_outside_allowed_root_is_rejected(
    tmp_path: Path,
):
    outside = (
        tmp_path.parent
        / "outside.csv"
    )

    try:
        _resolve_under_root(
            dataset_path=outside,
            allowed_root=tmp_path,
        )

    except ValueError as exc:
        assert (
            "outside the approved data directory"
            in str(exc)
        )

    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_successfully_loads_csv(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "plant.csv"
    )

    dataset.write_text(
        (
            "timestamp,feed_pressure,permeate_flow\n"
            "2026-10-24T10:00:00,60.5,120\n"
            "2026-10-24T10:05:00,61.0,118\n"
        ),
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path="plant.csv",
        allowed_root=tmp_path,
    )

    assert result["success"] is True
    assert result["recoverable"] is False

    assert (
        result["dataset_name"]
        == "plant.csv"
    )

    assert result["row_count"] == 2
    assert result["column_count"] == 3

    assert result["columns"] == [
        "timestamp",
        "feed_pressure",
        "permeate_flow",
    ]

    assert len(
        result["records"]
    ) == 2

    assert (
        result["records"][0]["feed_pressure"]
        == 60.5
    )


def test_missing_values_are_normalised(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "missing.csv"
    )

    dataset.write_text(
        (
            "pressure,flow\n"
            "60.0,120\n"
            ",118\n"
        ),
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path="missing.csv",
        allowed_root=tmp_path,
    )

    assert result["success"] is True

    assert (
        result["records"][1]["pressure"]
        is None
    )


def test_normalise_records_directly():
    import pandas as pd

    dataframe = pd.DataFrame(
        {
            "pressure": [
                60.0,
                None,
            ],
        }
    )

    result = _normalise_records(
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


def test_rejects_non_csv_file(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "plant.json"
    )

    dataset.write_text(
        "{}",
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path=dataset,
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Unsupported dataset type. "
            "Only CSV files are allowed."
        )
    )


def test_rejects_missing_file(
    tmp_path: Path,
):
    result = load_operational_data(
        state=make_state(),
        dataset_path="missing.csv",
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "Dataset file does not exist."
    )


def test_rejects_directory_as_dataset(
    tmp_path: Path,
):
    directory = (
        tmp_path / "fake.csv"
    )

    directory.mkdir()

    result = load_operational_data(
        state=make_state(),
        dataset_path=directory,
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Dataset path does not "
            "point to a file."
        )
    )


def test_rejects_oversized_dataset(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "large.csv"
    )

    dataset.write_text(
        "a,b\n1,2\n",
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path=dataset,
        allowed_root=tmp_path,
        max_file_size_bytes=1,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Dataset exceeds the "
            "configured file-size limit."
        )
    )


def test_rejects_empty_file(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "empty.csv"
    )

    dataset.write_text(
        "",
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path=dataset,
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        "Unable to read dataset:"
        in result["error"]
    )


def test_rejects_csv_with_headers_but_no_rows(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "headers.csv"
    )

    dataset.write_text(
        "pressure,flow\n",
        encoding="utf-8",
    )

    result = load_operational_data(
        state=make_state(),
        dataset_path=dataset,
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "Dataset contains no operational rows."
    )


def test_rejects_path_traversal(
    tmp_path: Path,
):
    result = load_operational_data(
        state=make_state(),
        dataset_path="../outside.csv",
        allowed_root=tmp_path,
    )

    assert result["success"] is False

    assert (
        "outside the approved data directory"
        in result["error"]
    )


def test_factory_creates_agent_compatible_tool(
    tmp_path: Path,
):
    dataset = (
        tmp_path / "plant.csv"
    )

    dataset.write_text(
        "pressure,flow\n60,120\n",
        encoding="utf-8",
    )

    tool = make_load_operational_data(
        dataset_path="plant.csv",
        allowed_root=tmp_path,
    )

    result = tool(
        make_state()
    )

    assert result["success"] is True
    assert result["row_count"] == 1