from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SEED = 42
DATA_DIR = Path("data")

START_TIME = "2026-10-01T00:00:00Z"
ROWS_PER_SCENARIO = 2016
FREQUENCY = "5min"


SCENARIOS: dict[str, dict[str, Any]] = {
    "normal_operation.csv": {
        "expected": "normal_operation",
        "flow_change": 0.5,
        "pressure_drop_change": 1.0,
        "rejection_change": 0.1,
        "sec_change": 1.0,
        "baseline_rejection": 99.0,
        "description": (
            "Stable synthetic RO operation with "
            "small measurement variation."
        ),
    },

    "scaling_colloidal_fouling.csv": {
        "expected": "scaling_or_colloidal_fouling",
        "flow_change": -18.0,
        "pressure_drop_change": 30.0,
        "rejection_change": -6.5,
        "sec_change": 18.0,
        "baseline_rejection": 99.0,
        "description": (
            "Progressive flow decline, rejection "
            "degradation, and pressure-drop increase."
        ),
    },

    "biofouling.csv": {
        "expected": "biofouling",
        "flow_change": -16.0,
        "pressure_drop_change": 30.0,
        "rejection_change": -0.3,
        "sec_change": 15.0,
        "baseline_rejection": 99.0,
        "description": (
            "Flow decline and pressure-drop increase "
            "with comparatively stable rejection."
        ),
    },

    "organic_fouling.csv": {
        "expected": "organic_fouling",
        "flow_change": -15.0,
        "pressure_drop_change": 2.0,
        "rejection_change": -0.2,
        "sec_change": 12.0,
        "baseline_rejection": 99.0,
        "description": (
            "Flow decline while pressure drop and "
            "rejection remain comparatively stable."
        ),
    },

    "membrane_integrity_issue.csv": {
        "expected": "membrane_integrity_or_seal_issue",
        "flow_change": 12.0,
        "pressure_drop_change": 2.0,
        "rejection_change": -7.0,
        "sec_change": -2.0,
        "baseline_rejection": 99.0,
        "description": (
            "Increased permeate flow accompanied by "
            "degraded salt rejection."
        ),
    },

    "compaction_mechanical_change.csv": {
        "expected": "compaction_or_mechanical_change",
        "flow_change": -15.0,
        "pressure_drop_change": 2.0,
        "rejection_change": 5.5,
        "sec_change": 10.0,
        "baseline_rejection": 94.0,
        "description": (
            "Flow decline with increased rejection "
            "and comparatively stable pressure drop."
        ),
    },

    "unclassified_abnormal.csv": {
        "expected": "unclassified",
        "flow_change": 14.0,
        "pressure_drop_change": 22.0,
        "rejection_change": 0.0,
        "sec_change": 12.0,
        "baseline_rejection": 99.0,
        "description": (
            "Abnormal combination deliberately outside "
            "the supported diagnostic patterns."
        ),
    },
}


def transition_factor(
    index: int,
    total_rows: int,
) -> float:
    """
    Three phases:

    0-35%:
        stable baseline

    35-85%:
        progressive change

    85-100%:
        established final condition
    """

    position = (
        index
        / max(
            total_rows - 1,
            1,
        )
    )

    if position <= 0.35:
        return 0.0

    if position >= 0.85:
        return 1.0

    return (
        position - 0.35
    ) / 0.50


def relative_change(
    baseline: float,
    change_pct: float,
    factor: float,
) -> float:
    """Apply a gradual percentage change."""

    return baseline * (
        1.0
        + (
            change_pct
            / 100.0
        )
        * factor
    )


def generate_scenario(
    config: dict[str, Any],
    seed: int,
) -> pd.DataFrame:
    """Generate one deterministic synthetic RO scenario."""

    rng = np.random.default_rng(
        seed
    )

    timestamps = pd.date_range(
        START_TIME,
        periods=ROWS_PER_SCENARIO,
        freq=FREQUENCY,
    )

    records: list[
        dict[str, Any]
    ] = []

    for index, timestamp in enumerate(
        timestamps
    ):
        factor = transition_factor(
            index,
            ROWS_PER_SCENARIO,
        )

        daily_phase = (
            2.0
            * np.pi
            * index
            / 288.0
        )

        feed_flow = (
            100.0
            + 0.45
            * np.sin(
                daily_phase
            )
            + rng.normal(
                0.0,
                0.12,
            )
        )

        feed_pressure = (
            60.0
            + 0.20
            * np.sin(
                daily_phase
                + 0.4
            )
            + rng.normal(
                0.0,
                0.05,
            )
        )

        feed_tds = (
            35000.0
            + 180.0
            * np.sin(
                daily_phase
                + 1.2
            )
            + rng.normal(
                0.0,
                35.0,
            )
        )

        baseline_permeate_flow = (
            45.0
            + 0.15
            * np.sin(
                daily_phase
                + 0.7
            )
        )

        permeate_flow = (
            relative_change(
                baseline_permeate_flow,
                float(
                    config[
                        "flow_change"
                    ]
                ),
                factor,
            )
            + rng.normal(
                0.0,
                0.05,
            )
        )

        pressure_drop = (
            relative_change(
                2.0,
                float(
                    config[
                        "pressure_drop_change"
                    ]
                ),
                factor,
            )
            + rng.normal(
                0.0,
                0.015,
            )
        )

        rejection = (
            relative_change(
                float(
                    config[
                        "baseline_rejection"
                    ]
                ),
                float(
                    config[
                        "rejection_change"
                    ]
                ),
                factor,
            )
            + rng.normal(
                0.0,
                0.015,
            )
        )

        rejection = float(
            np.clip(
                rejection,
                80.0,
                99.95,
            )
        )

        permeate_tds = (
            feed_tds
            * (
                1.0
                - rejection
                / 100.0
            )
        )

        concentrate_pressure = (
            feed_pressure
            - pressure_drop
        )

        concentrate_flow = (
            feed_flow
            - permeate_flow
        )

        recovery_rate_pct = (
            permeate_flow
            / feed_flow
            * 100.0
        )

        specific_energy = (
            relative_change(
                3.20,
                float(
                    config[
                        "sec_change"
                    ]
                ),
                factor,
            )
            + rng.normal(
                0.0,
                0.015,
            )
        )

        records.append(
            {
                "timestamp":
                    timestamp.isoformat(),

                "feed_flow":
                    round(
                        feed_flow,
                        4,
                    ),

                "permeate_flow":
                    round(
                        permeate_flow,
                        4,
                    ),

                "concentrate_flow":
                    round(
                        concentrate_flow,
                        4,
                    ),

                "feed_pressure":
                    round(
                        feed_pressure,
                        4,
                    ),

                "concentrate_pressure":
                    round(
                        concentrate_pressure,
                        4,
                    ),

                "feed_tds":
                    round(
                        feed_tds,
                        3,
                    ),

                "permeate_tds":
                    round(
                        permeate_tds,
                        3,
                    ),

                "recovery_rate_pct":
                    round(
                        recovery_rate_pct,
                        4,
                    ),

                "tds_salt_rejection_pct":
                    round(
                        rejection,
                        4,
                    ),

                "pressure_drop":
                    round(
                        pressure_drop,
                        4,
                    ),

                "differential_pressure":
                    round(
                        pressure_drop,
                        4,
                    ),

                "specific_energy_kwh_m3":
                    round(
                        specific_energy,
                        4,
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


def generate_corrupted_recoverable(
    source: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create an intentionally corrupted but recoverable
    sensor dataset.

    The corruption is deterministic and designed to
    exercise AquaMind validation/recovery behavior.
    """

    frame = source.copy()

    # -------------------------------------------------
    # Important for pandas 3.x:
    #
    # The clean source column is float64.
    # To intentionally inject a text sensor error,
    # explicitly make this column capable of mixed
    # values first.
    # -------------------------------------------------

    frame[
        "permeate_flow"
    ] = frame[
        "permeate_flow"
    ].astype(
        "object"
    )

    # Invalid timestamp.
    frame.loc[
        120,
        "timestamp",
    ] = "invalid-timestamp"

    # Invalid numeric sensor reading.
    frame.loc[
        300,
        "permeate_flow",
    ] = "not-a-number"

    # Missing readings.
    frame.loc[
        480,
        "permeate_tds",
    ] = np.nan

    frame.loc[
        620,
        "feed_pressure",
    ] = np.nan

    # Duplicate timestamp.
    duplicate = frame.iloc[
        [800]
    ].copy()

    numeric_flow = pd.to_numeric(
        duplicate[
            "permeate_flow"
        ],
        errors="coerce",
    )

    duplicate.loc[
        :,
        "permeate_flow",
    ] = (
        numeric_flow
        - 0.5
    )

    frame = pd.concat(
        [
            frame.iloc[
                :900
            ],
            duplicate,
            frame.iloc[
                900:
            ],
        ],
        ignore_index=True,
    )

    # Move a valid block to the end so the
    # timestamps are intentionally out of order.
    block = frame.iloc[
        1000:1010
    ].copy()

    frame = frame.drop(
        frame.index[
            1000:1010
        ]
    )

    frame = pd.concat(
        [
            frame,
            block,
        ],
        ignore_index=True,
    )

    return frame


def generate_insufficient_evidence(
) -> pd.DataFrame:
    """
    Valid schema but intentionally insufficient trend
    information for confident diagnosis.
    """

    timestamps = pd.date_range(
        START_TIME,
        periods=2,
        freq=FREQUENCY,
    )

    return pd.DataFrame(
        {
            "timestamp": [
                timestamp.isoformat()
                for timestamp
                in timestamps
            ],

            "feed_pressure": [
                60.0,
                60.1,
            ],

            "feed_flow": [
                100.0,
                100.1,
            ],
        }
    )


def write_csv(
    filename: str,
    frame: pd.DataFrame,
) -> None:
    """Write one scenario to the data directory."""

    output_path = (
        DATA_DIR
        / filename
    )

    frame.to_csv(
        output_path,
        index=False,
    )


def main() -> None:
    """Generate the complete AquaMind scenario bank."""

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated: dict[
        str,
        pd.DataFrame,
    ] = {}

    manifest: dict[
        str,
        Any,
    ] = {
        "dataset_type":
            "synthetic_ro_operational_scenarios",

        "real_plant_data":
            False,

        "generator_seed":
            SEED,

        "sampling_interval":
            FREQUENCY,

        "rows_per_standard_scenario":
            ROWS_PER_SCENARIO,

        "start_time":
            START_TIME,

        "purpose": (
            "Deterministic scenario bank for "
            "AquaMind AI development, system "
            "evaluation, and demonstration."
        ),

        "disclaimer": (
            "These datasets are synthetic. "
            "They must not be represented as "
            "telemetry collected from a real "
            "desalination plant."
        ),

        "scenarios": {},
    }

    for index, (
        filename,
        config,
    ) in enumerate(
        SCENARIOS.items()
    ):
        frame = generate_scenario(
            config,
            seed=(
                SEED
                + index
            ),
        )

        write_csv(
            filename,
            frame,
        )

        generated[
            filename
        ] = frame

        manifest[
            "scenarios"
        ][
            filename
        ] = {
            "expected":
                config[
                    "expected"
                ],

            "description":
                config[
                    "description"
                ],

            "rows":
                len(
                    frame
                ),

            "synthetic":
                True,
        }

    # -------------------------------------------------
    # Runtime compatibility scenario
    # -------------------------------------------------

    source_fault = (
        DATA_DIR
        / "scaling_colloidal_fouling.csv"
    )

    runtime_fault = (
        DATA_DIR
        / "membrane_fouling.csv"
    )

    shutil.copyfile(
        source_fault,
        runtime_fault,
    )

    manifest[
        "scenarios"
    ][
        "membrane_fouling.csv"
    ] = {
        "expected":
            "scaling_or_colloidal_fouling",

        "description":
            (
                "Compatibility alias used by "
                "the existing end-to-end "
                "runtime success test."
            ),

        "rows":
            ROWS_PER_SCENARIO,

        "synthetic":
            True,
    }

    # -------------------------------------------------
    # Recoverable data-quality scenario
    # -------------------------------------------------

    corrupted = (
        generate_corrupted_recoverable(
            generated[
                "scaling_colloidal_fouling.csv"
            ]
        )
    )

    write_csv(
        "corrupted_recoverable.csv",
        corrupted,
    )

    manifest[
        "scenarios"
    ][
        "corrupted_recoverable.csv"
    ] = {
        "expected":
            "validation_recovery",

        "description": (
            "Contains an invalid timestamp, "
            "non-numeric sensor reading, "
            "missing readings, duplicate "
            "timestamp, and out-of-order rows."
        ),

        "rows":
            len(
                corrupted
            ),

        "synthetic":
            True,
    }

    # -------------------------------------------------
    # Insufficient evidence scenario
    # -------------------------------------------------

    insufficient = (
        generate_insufficient_evidence()
    )

    write_csv(
        "insufficient_evidence.csv",
        insufficient,
    )

    manifest[
        "scenarios"
    ][
        "insufficient_evidence.csv"
    ] = {
        "expected":
            "insufficient_evidence",

        "description": (
            "Structurally valid dataset with "
            "too little trend information for "
            "a supported diagnosis."
        ),

        "rows":
            len(
                insufficient
            ),

        "synthetic":
            True,
    }

    # -------------------------------------------------
    # Manifest
    # -------------------------------------------------

    manifest_path = (
        DATA_DIR
        / "scenario_manifest.json"
    )

    with manifest_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        "AquaMind synthetic scenario bank generated."
    )

    print(
        "Synthetic data only - "
        "not real plant telemetry."
    )

    print()

    total_rows = 0

    for path in sorted(
        DATA_DIR.glob(
            "*.csv"
        )
    ):
        frame = pd.read_csv(
            path
        )

        row_count = len(
            frame
        )

        total_rows += (
            row_count
        )

        print(
            f"{path.name}: "
            f"{row_count:,} rows"
        )

    print()
    print(
        f"Total generated CSV rows: "
        f"{total_rows:,}"
    )

    print(
        "Manifest: "
        "data/scenario_manifest.json"
    )


if __name__ == "__main__":
    main()