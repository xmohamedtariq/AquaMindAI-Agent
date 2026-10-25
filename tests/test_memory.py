from pathlib import Path

from src.agent.state import AgentState
from src.memory.sqlite_memory import (
    IncidentMemory,
    _latest_diagnosis,
    make_save_incident,
    make_search_incident_memory,
    save_incident_from_state,
    search_incident_memory_from_state,
)


def make_memory(
    tmp_path: Path,
) -> IncidentMemory:
    return IncidentMemory(
        tmp_path
        / "memory"
        / "incidents.db"
    )


def make_state() -> AgentState:
    return AgentState(
        task_id="memory-test",
        user_request=(
            "Investigate RO degradation"
        ),
        plant_id="plant-a",
    )


def sample_incident(
    memory: IncidentMemory,
    *,
    incident_id: str = "incident-1",
    plant_id: str = "plant-a",
    diagnosis_id: str = "biofouling",
    summary: str = (
        "Possible biofouling pattern."
    ),
):
    return memory.save_incident(
        incident_id=incident_id,
        plant_id=plant_id,
        diagnosis_id=diagnosis_id,
        severity="warning",
        confidence=0.74,
        summary=summary,
        evidence=[
            {
                "metric":
                    "pressure_drop",
                "change_pct":
                    12.0,
            }
        ],
        recommendations=[
            (
                "Review pretreatment "
                "performance."
            )
        ],
        metadata={
            "source":
                "test",
        },
    )


def diagnosis_result():
    return {
        "success": True,
        "diagnosis_status":
            "hypothesis_generated",
        "conclusion":
            (
                "A supported RO troubleshooting "
                "pattern was identified."
            ),
        "primary_hypothesis": {
            "id":
                "biofouling",
            "severity":
                "warning",
            "confidence":
                0.74,
            "evidence": [
                {
                    "metric":
                        "pressure_drop",
                    "change_pct":
                        12.0,
                }
            ],
            "verification_steps": [
                (
                    "Review pretreatment "
                    "history."
                )
            ],
        },
    }


def test_database_initializes(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    assert (
        memory.db_path.exists()
        is True
    )

    assert (
        memory.count_incidents()
        == 0
    )


def test_save_and_get_incident(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = sample_incident(
        memory
    )

    assert result[
        "success"
    ] is True

    stored = memory.get_incident(
        "incident-1"
    )

    assert stored is not None

    assert (
        stored["plant_id"]
        == "plant-a"
    )

    assert (
        stored["diagnosis_id"]
        == "biofouling"
    )

    assert (
        stored["confidence"]
        == 0.74
    )

    assert stored[
        "evidence"
    ][0]["metric"] == (
        "pressure_drop"
    )

    assert stored[
        "recommendations"
    ] == [
        (
            "Review pretreatment "
            "performance."
        )
    ]

    assert (
        stored["metadata"][
            "source"
        ]
        == "test"
    )

    assert (
        stored["created_at"]
        .endswith("Z")
    )


def test_memory_persists_between_instances(
    tmp_path: Path,
):
    db_path = (
        tmp_path
        / "incidents.db"
    )

    first = IncidentMemory(
        db_path
    )

    sample_incident(
        first
    )

    second = IncidentMemory(
        db_path
    )

    assert (
        second.count_incidents()
        == 1
    )

    assert (
        second.get_incident(
            "incident-1"
        )["diagnosis_id"]
        == "biofouling"
    )


def test_missing_incident_returns_none(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    assert (
        memory.get_incident(
            "missing"
        )
        is None
    )


def test_incident_id_is_required(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = sample_incident(
        memory,
        incident_id=" ",
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == "Incident ID is required."
    )


def test_plant_id_is_required(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = sample_incident(
        memory,
        plant_id=" ",
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == "Plant ID is required."
    )


def test_diagnosis_id_is_required(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = sample_incident(
        memory,
        diagnosis_id=" ",
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == "Diagnosis ID is required."
    )


def test_confidence_must_be_numeric(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = memory.save_incident(
        incident_id="bad-confidence",
        plant_id="plant-a",
        diagnosis_id="biofouling",
        severity="warning",
        confidence="bad",
        summary="test",
        evidence=[],
        recommendations=[],
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == (
            "Confidence must be "
            "a numeric value."
        )
    )


def test_confidence_below_range_fails(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = memory.save_incident(
        incident_id="negative",
        plant_id="plant-a",
        diagnosis_id="biofouling",
        severity="warning",
        confidence=-0.1,
        summary="test",
        evidence=[],
        recommendations=[],
    )

    assert result[
        "success"
    ] is False


def test_confidence_above_range_fails(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = memory.save_incident(
        incident_id="high",
        plant_id="plant-a",
        diagnosis_id="biofouling",
        severity="warning",
        confidence=1.1,
        summary="test",
        evidence=[],
        recommendations=[],
    )

    assert result[
        "success"
    ] is False


def test_duplicate_incident_is_rejected(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    first = sample_incident(
        memory
    )

    second = sample_incident(
        memory
    )

    assert first[
        "success"
    ] is True

    assert second[
        "success"
    ] is False

    assert (
        second["error"]
        == (
            "An incident with this ID "
            "already exists."
        )
    )


def test_search_all_incidents(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory,
        incident_id="one",
    )

    sample_incident(
        memory,
        incident_id="two",
        plant_id="plant-b",
        diagnosis_id="scaling",
        summary=(
            "Possible scaling pattern."
        ),
    )

    result = memory.search_incidents()

    assert result[
        "success"
    ] is True

    assert (
        result["match_count"]
        == 2
    )


def test_search_by_plant(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory,
        incident_id="one",
        plant_id="plant-a",
    )

    sample_incident(
        memory,
        incident_id="two",
        plant_id="plant-b",
    )

    result = memory.search_incidents(
        plant_id="plant-a"
    )

    assert (
        result["match_count"]
        == 1
    )

    assert (
        result["incidents"][0]
        ["plant_id"]
        == "plant-a"
    )


def test_search_by_text(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory,
        incident_id="one",
        diagnosis_id="biofouling",
        summary=(
            "Possible biological fouling."
        ),
    )

    sample_incident(
        memory,
        incident_id="two",
        diagnosis_id="scaling",
        summary=(
            "Possible mineral deposition."
        ),
    )

    result = memory.search_incidents(
        query="scaling"
    )

    assert (
        result["match_count"]
        == 1
    )

    assert (
        result["incidents"][0]
        ["diagnosis_id"]
        == "scaling"
    )


def test_search_limit(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory,
        incident_id="one",
    )

    sample_incident(
        memory,
        incident_id="two",
    )

    result = memory.search_incidents(
        limit=1
    )

    assert (
        result["match_count"]
        == 1
    )


def test_invalid_search_limit_fails(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = memory.search_incidents(
        limit=0
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == (
            "Search limit must be "
            "greater than zero."
        )
    )


def test_latest_diagnosis_covers_skips():
    state = make_state()

    expected = diagnosis_result()

    state.add_observation(
        source="diagnose_issue",
        content=expected,
    )

    state.add_observation(
        source="diagnose_issue",
        content={
            "success": False,
        },
    )

    state.add_observation(
        source="diagnose_issue",
        content="bad-content",
    )

    state.add_observation(
        source="other_tool",
        content={
            "success": True,
        },
    )

    assert (
        _latest_diagnosis(
            state
        )
        == expected
    )


def test_latest_diagnosis_can_be_missing():
    assert (
        _latest_diagnosis(
            make_state()
        )
        is None
    )


def test_search_memory_from_state(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory,
        incident_id="one",
        plant_id="plant-a",
    )

    sample_incident(
        memory,
        incident_id="two",
        plant_id="plant-b",
    )

    result = (
        search_incident_memory_from_state(
            state=make_state(),
            memory=memory,
        )
    )

    assert (
        result["match_count"]
        == 1
    )

    assert (
        result["incidents"][0]
        ["plant_id"]
        == "plant-a"
    )


def test_save_requires_human_approval(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = save_incident_from_state(
        state=make_state(),
        memory=memory,
        approved=False,
    )

    assert result[
        "success"
    ] is False

    assert result[
        "_permission_required"
    ] is True

    assert (
        result[
            "permission_level"
        ]
        == "ASK_ON_WRITE"
    )


def test_save_fails_without_diagnosis(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    result = save_incident_from_state(
        state=make_state(),
        memory=memory,
        approved=True,
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == (
            "Successful diagnosis evidence "
            "is unavailable."
        )
    )


def test_save_requires_primary_hypothesis(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    state = make_state()

    state.add_observation(
        source="diagnose_issue",
        content={
            "success": True,
            "primary_hypothesis":
                None,
        },
    )

    result = save_incident_from_state(
        state=state,
        memory=memory,
        approved=True,
    )

    assert result[
        "success"
    ] is False

    assert (
        result["error"]
        == (
            "A primary diagnostic "
            "hypothesis is required."
        )
    )


def test_save_handles_invalid_evidence_and_recommendations(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    state = make_state()

    diagnosis = diagnosis_result()

    diagnosis[
        "primary_hypothesis"
    ]["evidence"] = "bad"

    diagnosis[
        "primary_hypothesis"
    ][
        "verification_steps"
    ] = "bad"

    state.add_observation(
        source="diagnose_issue",
        content=diagnosis,
    )

    result = save_incident_from_state(
        state=state,
        memory=memory,
        approved=True,
    )

    assert result[
        "success"
    ] is True

    stored = memory.get_incident(
        "memory-test-incident"
    )

    assert (
        stored["evidence"]
        == []
    )

    assert (
        stored["recommendations"]
        == []
    )


def test_save_incident_from_state_success(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    state = make_state()

    state.add_observation(
        source="diagnose_issue",
        content=diagnosis_result(),
    )

    result = save_incident_from_state(
        state=state,
        memory=memory,
        approved=True,
    )

    assert result[
        "success"
    ] is True

    assert (
        memory.count_incidents()
        == 1
    )

    stored = memory.get_incident(
        "memory-test-incident"
    )

    assert (
        stored["diagnosis_id"]
        == "biofouling"
    )

    assert (
        stored["plant_id"]
        == "plant-a"
    )


def test_search_factory(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    sample_incident(
        memory
    )

    tool = make_search_incident_memory(
        memory,
        limit=3,
    )

    result = tool(
        make_state()
    )

    assert (
        result["match_count"]
        == 1
    )


def test_save_factory_without_approval(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    tool = make_save_incident(
        memory,
        approved=False,
    )

    result = tool(
        make_state()
    )

    assert result[
        "_permission_required"
    ] is True


def test_save_factory_with_approval(
    tmp_path: Path,
):
    memory = make_memory(
        tmp_path
    )

    state = make_state()

    state.add_observation(
        source="diagnose_issue",
        content=diagnosis_result(),
    )

    tool = make_save_incident(
        memory,
        approved=True,
    )

    result = tool(
        state
    )

    assert result[
        "success"
    ] is True

    assert (
        memory.count_incidents()
        == 1
    )