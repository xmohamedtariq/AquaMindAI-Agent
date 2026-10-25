from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.knowledge.case_library import (
    CaseLibraryError,
    load_case_library,
    load_source_ids,
    source_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "knowledge" / "case_library.json"
REGISTRY = ROOT / "knowledge" / "source_registry.json"


def write_json(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def minimal_source_registry():
    return {"sources": [{"id": "SRC-1"}, {"id": "SRC-2"}]}


def minimal_case(**overrides):
    item = {
        "case_id": "CASE-1",
        "title": "Case",
        "domain": "domain",
        "category": "category",
        "expected_label": "label",
        "intent": "diagnosis",
        "observed_patterns": ["pattern"],
        "reasoning_basis": ["reason"],
        "source_ids": ["SRC-1"],
        "support_level": "direct",
        "confidence_type": "source_grounded_heuristic",
        "implementation_status": "knowledge_grounded",
        "verification_required": True,
        "physical_action_authorized": False,
        "inference_note": "verify",
        "synthetic_variation_axes": [],
    }
    item.update(overrides)
    return item


def minimal_library(cases=None, count=None):
    values = cases if cases is not None else [minimal_case()]
    return {
        "library_version": "1.0",
        "case_count": len(values) if count is None else count,
        "cases": values,
    }


def test_real_library_loads_and_is_source_traceable():
    library = load_case_library(LIBRARY, REGISTRY)
    source_ids = load_source_ids(REGISTRY)

    assert len(library.cases) == 90
    assert library.version == "1.0.0"
    assert all(case.source_ids for case in library.cases)
    assert all(not case.physical_action_authorized for case in library.cases)

    coverage = source_coverage(library, source_ids)
    assert coverage["unknown"] == ()
    assert "DUPONT_RO_MANUAL_V20_2026" in coverage["used"]
    assert "TORAY_RO_HANDLING_MANUAL_2025" in coverage["used"]


def test_find_and_get_filters():
    library = load_case_library(LIBRARY, REGISTRY)

    scaling = library.find(category="scaling")
    assert scaling
    assert all(item.category == "scaling" for item in scaling)

    secured = library.find(
        domain="agent_ot_security",
        implementation_status="safety_policy",
    )
    assert secured
    assert all(item.domain == "agent_ot_security" for item in secured)

    source_cases = library.find(source_id="ASTM_D4516_19A")
    assert source_cases

    label_cases = library.find(expected_label="biofouling")
    assert label_cases

    item = library.get("RO-SCALE-001")
    assert item is not None
    assert item.case_id == "RO-SCALE-001"
    assert library.get("DOES-NOT-EXIST") is None

    assert library.find(domain="does-not-exist") == ()
    assert library.find(category="does-not-exist") == ()
    assert library.find(expected_label="does-not-exist") == ()
    assert library.find(source_id="does-not-exist") == ()
    assert library.find(implementation_status="does-not-exist") == ()


def test_source_coverage_reports_unused_and_unknown():
    library = load_case_library(LIBRARY, REGISTRY)
    result = source_coverage(library, {"EXTRA"})
    assert "EXTRA" in result["unused"]
    assert result["unknown"]


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "{bad json",
    ],
)
def test_invalid_json_roots_and_syntax(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(CaseLibraryError):
        load_source_ids(path)


def test_missing_json_file():
    with pytest.raises(CaseLibraryError):
        load_source_ids("missing-registry.json")


def test_unreadable_json_is_wrapped(tmp_path, monkeypatch):
    path = tmp_path / "registry.json"
    path.write_text("{}", encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_text", boom)
    with pytest.raises(CaseLibraryError):
        load_source_ids(path)


@pytest.mark.parametrize(
    "registry",
    [
        {},
        {"sources": []},
        {"sources": ["bad"]},
        {"sources": [{"id": ""}]},
        {"sources": [{"id": "X"}, {"id": "X"}]},
    ],
)
def test_invalid_source_registry(tmp_path, registry):
    path = write_json(tmp_path / "registry.json", registry)
    with pytest.raises(CaseLibraryError):
        load_source_ids(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", ""),
        ("title", ""),
        ("domain", ""),
        ("category", ""),
        ("expected_label", ""),
        ("intent", ""),
        ("confidence_type", ""),
        ("inference_note", ""),
        ("observed_patterns", "bad"),
        ("observed_patterns", []),
        ("reasoning_basis", "bad"),
        ("reasoning_basis", []),
        ("source_ids", "bad"),
        ("source_ids", []),
        ("synthetic_variation_axes", "bad"),
        ("verification_required", "yes"),
        ("physical_action_authorized", "no"),
    ],
)
def test_invalid_case_fields(tmp_path, field, value):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    data = minimal_library([minimal_case(**{field: value})])
    library = write_json(tmp_path / "library.json", data)
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


def test_non_string_item_in_text_list(tmp_path):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    data = minimal_library([minimal_case(observed_patterns=[1])])
    library = write_json(tmp_path / "library.json", data)
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


@pytest.mark.parametrize(
    "changes",
    [
        {"source_ids": ["UNKNOWN"]},
        {"support_level": "invalid"},
        {"implementation_status": "invalid"},
        {"physical_action_authorized": True},
    ],
)
def test_invalid_case_semantics(tmp_path, changes):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    library = write_json(
        tmp_path / "library.json",
        minimal_library([minimal_case(**changes)]),
    )
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


def test_case_must_be_object(tmp_path):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    library = write_json(
        tmp_path / "library.json",
        {"library_version": "1", "case_count": 1, "cases": ["bad"]},
    )
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


@pytest.mark.parametrize(
    "library_data",
    [
        {},
        {"library_version": "", "case_count": 0, "cases": []},
        {"library_version": "1", "case_count": 0, "cases": "bad"},
        {"library_version": "1", "case_count": 0, "cases": []},
    ],
)
def test_invalid_library_structure(tmp_path, library_data):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    library = write_json(tmp_path / "library.json", library_data)
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


def test_duplicate_case_id(tmp_path):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    first = minimal_case()
    second = minimal_case(title="Another")
    library = write_json(
        tmp_path / "library.json",
        minimal_library([first, second]),
    )
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)


def test_case_count_mismatch(tmp_path):
    registry = write_json(tmp_path / "registry.json", minimal_source_registry())
    library = write_json(
        tmp_path / "library.json",
        minimal_library(count=99),
    )
    with pytest.raises(CaseLibraryError):
        load_case_library(library, registry)
