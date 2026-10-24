from math import inf, nan

from src.agent.state import AgentState
from src.tools.kpi_tools import (
    KPI_NAMES,
    _calculate_flow_balance_error,
    _calculate_pressure_drop,
    _calculate_recovery,
    _calculate_rejection,
    _column_values,
    _latest_validated_records,
    _summary,
    _to_finite_float,
    calculate_plant_kpis,
    calculate_plant_kpis_from_state,
    make_calculate_plant_kpis,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="kpi-test",
        user_request=(
            "Calculate desalination plant KPIs"
        ),
    )


def full_records():
    return [
        {
            "timestamp":
                "2026-10-24T10:00:00Z",
            "feed_flow": 200.0,
            "permeate_flow": 90.0,
            "concentrate_flow": 110.0,
            "feed_pressure": 60.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 350.0,
            "feed_conductivity": 52000.0,
            "permeate_conductivity": 600.0,
            "recovery_rate": 45.0,
            "differential_pressure": 3.0,
            "specific_energy_consumption": 3.2,
        },
        {
            "timestamp":
                "2026-10-24T10:05:00Z",
            "feed_flow": 200.0,
            "permeate_flow": 88.0,
            "concentrate_flow": 111.0,
            "feed_pressure": 61.0,
            "concentrate_pressure": 57.5,
            "feed_tds": 35200.0,
            "permeate_tds": 400.0,
            "feed_conductivity": 52500.0,
            "permeate_conductivity": 650.0,
            "recovery_rate": 44.0,
            "differential_pressure": 3.5,
            "specific_energy_consumption": 3.4,
        },
    ]


def test_to_finite_float():
    assert _to_finite_float(10) == 10.0

    assert (
        _to_finite_float("12.5")
        == 12.5
    )

    assert (
        _to_finite_float(None)
        is None
    )

    assert (
        _to_finite_float("invalid")
        is None
    )

    assert (
        _to_finite_float(nan)
        is None
    )

    assert (
        _to_finite_float(inf)
        is None
    )


def test_summary():
    assert (
        _summary([])
        is None
    )

    result = _summary(
        [
            1.0,
            2.0,
            3.0,
        ]
    )

    assert result == {
        "count": 3,
        "average": 2.0,
        "minimum": 1.0,
        "maximum": 3.0,
        "latest": 3.0,
    }


def test_column_values_ignores_invalid_values():
    records = [
        {
            "value": 10,
        },
        {
            "value": None,
        },
        {
            "value": "bad",
        },
        {
            "value": 20,
        },
    ]

    assert (
        _column_values(
            records,
            "value",
        )
        == [
            10.0,
            20.0,
        ]
    )


def test_calculate_recovery():
    records = [
        {
            "feed_flow": 200,
            "permeate_flow": 90,
        },
        {
            "feed_flow": 100,
            "permeate_flow": 40,
        },
    ]

    result = _calculate_recovery(
        records
    )

    assert result == [
        45.0,
        40.0,
    ]


def test_recovery_skips_missing_and_invalid_feed():
    records = [
        {
            "feed_flow": None,
            "permeate_flow": 40,
        },
        {
            "feed_flow": 0,
            "permeate_flow": 40,
        },
        {
            "feed_flow": -100,
            "permeate_flow": 40,
        },
        {
            "feed_flow": 100,
            "permeate_flow": None,
        },
    ]

    assert (
        _calculate_recovery(
            records
        )
        == []
    )


def test_calculate_tds_rejection():
    result = _calculate_rejection(
        records=[
            {
                "feed_tds": 35000,
                "permeate_tds": 350,
            }
        ],
        feed_column="feed_tds",
        permeate_column="permeate_tds",
    )

    assert result == [
        99.0
    ]


def test_rejection_skips_missing_and_invalid_feed():
    records = [
        {
            "feed_tds": None,
            "permeate_tds": 100,
        },
        {
            "feed_tds": 0,
            "permeate_tds": 100,
        },
        {
            "feed_tds": -1,
            "permeate_tds": 100,
        },
        {
            "feed_tds": 1000,
            "permeate_tds": None,
        },
    ]

    assert (
        _calculate_rejection(
            records=records,
            feed_column="feed_tds",
            permeate_column="permeate_tds",
        )
        == []
    )


def test_calculate_pressure_drop():
    result = _calculate_pressure_drop(
        [
            {
                "feed_pressure": 60,
                "concentrate_pressure": 57,
            },
            {
                "feed_pressure": 61,
                "concentrate_pressure": 57.5,
            },
        ]
    )

    assert result == [
        3.0,
        3.5,
    ]


def test_pressure_drop_skips_missing_values():
    result = _calculate_pressure_drop(
        [
            {
                "feed_pressure": None,
                "concentrate_pressure": 57,
            },
            {
                "feed_pressure": 60,
                "concentrate_pressure": None,
            },
        ]
    )

    assert result == []


def test_flow_balance_error():
    result = _calculate_flow_balance_error(
        [
            {
                "feed_flow": 200,
                "permeate_flow": 90,
                "concentrate_flow": 110,
            },
            {
                "feed_flow": 200,
                "permeate_flow": 88,
                "concentrate_flow": 111,
            },
        ]
    )

    assert result == [
        0.0,
        0.5,
    ]


def test_flow_balance_skips_incomplete_and_invalid_rows():
    records = [
        {
            "feed_flow": None,
            "permeate_flow": 50,
            "concentrate_flow": 50,
        },
        {
            "feed_flow": 100,
            "permeate_flow": None,
            "concentrate_flow": 50,
        },
        {
            "feed_flow": 100,
            "permeate_flow": 50,
            "concentrate_flow": None,
        },
        {
            "feed_flow": 0,
            "permeate_flow": 50,
            "concentrate_flow": 50,
        },
    ]

    assert (
        _calculate_flow_balance_error(
            records
        )
        == []
    )


def test_empty_records_fail():
    result = calculate_plant_kpis(
        []
    )

    assert result["success"] is False
    assert result["recoverable"] is False

    assert (
        result["error"]
        == (
            "No validated sensor records "
            "were provided for KPI calculation."
        )
    )


def test_complete_kpi_calculation():
    result = calculate_plant_kpis(
        full_records()
    )

    assert result["success"] is True
    assert result["record_count"] == 2

    kpis = result["kpis"]

    assert (
        kpis[
            "calculated_recovery_rate_pct"
        ]["average"]
        == 44.5
    )

    assert (
        kpis[
            "calculated_pressure_drop"
        ]["latest"]
        == 3.5
    )

    assert (
        kpis[
            "flow_balance_error_pct"
        ]["maximum"]
        == 0.5
    )

    assert (
        kpis[
            "reported_recovery_rate_pct"
        ]["average"]
        == 44.5
    )

    assert (
        kpis[
            "reported_differential_pressure"
        ]["latest"]
        == 3.5
    )

    assert (
        kpis[
            "specific_energy_consumption"
        ]["average"]
        == 3.3
    )

    assert (
        "conductivity_rejection_estimate_pct"
        in result["available_kpis"]
    )

    assert (
        "Conductivity-based rejection is "
        "reported as an operational estimate."
        in result["notes"]
    )


def test_missing_optional_kpis_are_reported():
    records = [
        {
            "timestamp":
                "2026-10-24T10:00:00Z",
            "feed_pressure": 60,
        }
    ]

    result = calculate_plant_kpis(
        records
    )

    assert result["success"] is True

    assert (
        result["available_kpis"]
        == []
    )

    assert set(
        result["unavailable_kpis"]
    ) == set(
        KPI_NAMES
    )

    assert (
        "Specific energy consumption was "
        "not derived from generic energy data "
        "because the required units and time "
        "basis were not explicitly available."
        in result["notes"]
    )


def test_specific_energy_note_not_added_when_available():
    result = calculate_plant_kpis(
        [
            {
                "specific_energy_consumption": 3.5,
            }
        ]
    )

    assert (
        result["kpis"][
            "specific_energy_consumption"
        ]["average"]
        == 3.5
    )

    assert not any(
        note.startswith(
            "Specific energy consumption was"
        )
        for note in result["notes"]
    )


def test_latest_validated_records_covers_skipped_observations():
    """
    The valid observation is intentionally added first.

    Because the implementation reads observations
    in reverse order, it must skip:
    - unrelated source
    - non-dict content
    - unsuccessful validation

    before reaching the valid records.
    """

    state = make_state()

    expected = [
        {
            "feed_flow": 200,
            "permeate_flow": 90,
        }
    ]

    # Valid observation added FIRST.
    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": expected,
        },
    )

    # Unsuccessful validation must be skipped.
    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": False,
            "records": [],
        },
    )

    # Invalid content type must be skipped.
    state.add_observation(
        source="validate_sensor_data",
        content="invalid-content",
    )

    # Unrelated tool must be skipped.
    state.add_observation(
        source="other_tool",
        content={
            "success": True,
            "records": [
                {
                    "feed_flow": 1,
                }
            ],
        },
    )

    assert (
        _latest_validated_records(
            state
        )
        == expected
    )


def test_latest_validation_requires_list_records():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": "not-a-list",
        },
    )

    assert (
        _latest_validated_records(
            state
        )
        is None
    )


def test_kpi_from_state_without_validation_fails():
    state = make_state()

    result = calculate_plant_kpis_from_state(
        state
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Validated sensor records are "
            "unavailable in agent observations."
        )
    )


def test_kpi_from_state_success():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": full_records(),
        },
    )

    result = calculate_plant_kpis_from_state(
        state
    )

    assert result["success"] is True

    assert (
        "calculated_recovery_rate_pct"
        in result["available_kpis"]
    )


def test_factory_returns_agent_tool():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": full_records(),
        },
    )

    tool = make_calculate_plant_kpis()

    result = tool(
        state
    )

    assert result["success"] is True
    assert result["record_count"] == 2