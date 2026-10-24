from collections.abc import Callable
from math import isfinite
from typing import Any

from src.agent.state import AgentState


VALIDATION_SOURCE = "validate_sensor_data"


KPI_NAMES = (
    "calculated_recovery_rate_pct",
    "tds_salt_rejection_pct",
    "conductivity_rejection_estimate_pct",
    "calculated_pressure_drop",
    "flow_balance_error_pct",
    "reported_recovery_rate_pct",
    "reported_differential_pressure",
    "specific_energy_consumption",
)


def _to_finite_float(
    value: Any,
) -> float | None:
    """
    Convert a value to a finite float.

    Invalid, missing, infinite, or NaN values
    are ignored safely.
    """

    if value is None:
        return None

    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not isfinite(
        number
    ):
        return None

    return number


def _summary(
    values: list[float],
) -> dict[str, float | int] | None:
    """
    Produce a compact numeric KPI summary.
    """

    if not values:
        return None

    return {
        "count": len(values),
        "average": round(
            sum(values)
            / len(values),
            4,
        ),
        "minimum": round(
            min(values),
            4,
        ),
        "maximum": round(
            max(values),
            4,
        ),
        "latest": round(
            values[-1],
            4,
        ),
    }


def _column_values(
    records: list[dict[str, Any]],
    column: str,
) -> list[float]:
    """
    Extract valid numeric values from a column.
    """

    values: list[float] = []

    for record in records:

        value = _to_finite_float(
            record.get(
                column
            )
        )

        if value is not None:
            values.append(
                value
            )

    return values


def _calculate_recovery(
    records: list[dict[str, Any]],
) -> list[float]:
    """
    Calculate RO recovery:

    permeate flow / feed flow * 100
    """

    values: list[float] = []

    for record in records:

        feed_flow = _to_finite_float(
            record.get(
                "feed_flow"
            )
        )

        permeate_flow = _to_finite_float(
            record.get(
                "permeate_flow"
            )
        )

        if (
            feed_flow is None
            or permeate_flow is None
        ):
            continue

        if feed_flow <= 0:
            continue

        recovery = (
            permeate_flow
            / feed_flow
            * 100.0
        )

        values.append(
            recovery
        )

    return values


def _calculate_rejection(
    records: list[dict[str, Any]],
    feed_column: str,
    permeate_column: str,
) -> list[float]:
    """
    Calculate solute rejection:

    (1 - permeate / feed) * 100
    """

    values: list[float] = []

    for record in records:

        feed_value = _to_finite_float(
            record.get(
                feed_column
            )
        )

        permeate_value = _to_finite_float(
            record.get(
                permeate_column
            )
        )

        if (
            feed_value is None
            or permeate_value is None
        ):
            continue

        if feed_value <= 0:
            continue

        rejection = (
            1.0
            - (
                permeate_value
                / feed_value
            )
        ) * 100.0

        values.append(
            rejection
        )

    return values


def _calculate_pressure_drop(
    records: list[dict[str, Any]],
) -> list[float]:
    """
    Calculate pressure drop:

    feed pressure - concentrate pressure

    Input pressures must use consistent units.
    """

    values: list[float] = []

    for record in records:

        feed_pressure = _to_finite_float(
            record.get(
                "feed_pressure"
            )
        )

        concentrate_pressure = _to_finite_float(
            record.get(
                "concentrate_pressure"
            )
        )

        if (
            feed_pressure is None
            or concentrate_pressure is None
        ):
            continue

        values.append(
            feed_pressure
            - concentrate_pressure
        )

    return values


def _calculate_flow_balance_error(
    records: list[dict[str, Any]],
) -> list[float]:
    """
    Calculate relative flow-balance error:

    abs(feed - permeate - concentrate)
    / feed * 100
    """

    values: list[float] = []

    for record in records:

        feed_flow = _to_finite_float(
            record.get(
                "feed_flow"
            )
        )

        permeate_flow = _to_finite_float(
            record.get(
                "permeate_flow"
            )
        )

        concentrate_flow = _to_finite_float(
            record.get(
                "concentrate_flow"
            )
        )

        if (
            feed_flow is None
            or permeate_flow is None
            or concentrate_flow is None
        ):
            continue

        if feed_flow <= 0:
            continue

        error = (
            abs(
                feed_flow
                - permeate_flow
                - concentrate_flow
            )
            / feed_flow
            * 100.0
        )

        values.append(
            error
        )

    return values


def calculate_plant_kpis(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate defensible RO operational KPIs.

    Missing measurements do not cause fabricated
    values. Unavailable KPIs are reported explicitly.
    """

    if not records:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "No validated sensor records "
                "were provided for KPI calculation."
            ),
        }

    recovery = _summary(
        _calculate_recovery(
            records
        )
    )

    tds_rejection = _summary(
        _calculate_rejection(
            records=records,
            feed_column="feed_tds",
            permeate_column="permeate_tds",
        )
    )

    conductivity_rejection = _summary(
        _calculate_rejection(
            records=records,
            feed_column="feed_conductivity",
            permeate_column="permeate_conductivity",
        )
    )

    pressure_drop = _summary(
        _calculate_pressure_drop(
            records
        )
    )

    flow_balance_error = _summary(
        _calculate_flow_balance_error(
            records
        )
    )

    reported_recovery = _summary(
        _column_values(
            records,
            "recovery_rate",
        )
    )

    reported_differential_pressure = _summary(
        _column_values(
            records,
            "differential_pressure",
        )
    )

    specific_energy = _summary(
        _column_values(
            records,
            "specific_energy_consumption",
        )
    )

    kpis = {
        "calculated_recovery_rate_pct":
            recovery,

        "tds_salt_rejection_pct":
            tds_rejection,

        "conductivity_rejection_estimate_pct":
            conductivity_rejection,

        "calculated_pressure_drop":
            pressure_drop,

        "flow_balance_error_pct":
            flow_balance_error,

        "reported_recovery_rate_pct":
            reported_recovery,

        "reported_differential_pressure":
            reported_differential_pressure,

        "specific_energy_consumption":
            specific_energy,
    }

    available_kpis = [
        name
        for name, value in kpis.items()
        if value is not None
    ]

    unavailable_kpis = [
        name
        for name, value in kpis.items()
        if value is None
    ]

    notes: list[str] = []

    if conductivity_rejection is not None:
        notes.append(
            (
                "Conductivity-based rejection is "
                "reported as an operational estimate."
            )
        )

    if specific_energy is None:
        notes.append(
            (
                "Specific energy consumption was "
                "not derived from generic energy data "
                "because the required units and time "
                "basis were not explicitly available."
            )
        )

    return {
        "success": True,
        "recoverable": False,
        "record_count": len(
            records
        ),
        "kpis": kpis,
        "available_kpis": (
            available_kpis
        ),
        "unavailable_kpis": (
            unavailable_kpis
        ),
        "notes": notes,
    }


def _latest_validated_records(
    state: AgentState,
) -> list[dict[str, Any]] | None:
    """
    Retrieve the latest successful validation
    records from agent observations.
    """

    for observation in reversed(
        state.observations
    ):

        if (
            observation.get(
                "source"
            )
            != VALIDATION_SOURCE
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

        if content.get(
            "success"
        ) is not True:
            continue

        records = content.get(
            "records"
        )

        if isinstance(
            records,
            list,
        ):
            return records

    return None


def calculate_plant_kpis_from_state(
    state: AgentState,
) -> dict[str, Any]:
    """
    AgentLoop-compatible KPI tool.

    Reads the latest validated sensor records
    already stored in the current investigation.
    """

    records = _latest_validated_records(
        state
    )

    if records is None:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Validated sensor records are "
                "unavailable in agent observations."
            ),
        }

    return calculate_plant_kpis(
        records
    )


def make_calculate_plant_kpis(
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """
    Create an AgentLoop-compatible KPI tool.
    """

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return calculate_plant_kpis_from_state(
            state
        )

    return tool