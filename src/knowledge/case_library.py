from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class CaseLibraryError(ValueError):
    """Raised when the case library or source registry is invalid."""


@dataclass(frozen=True)
class KnowledgeCase:
    case_id: str
    title: str
    domain: str
    category: str
    expected_label: str
    intent: str
    observed_patterns: tuple[str, ...]
    reasoning_basis: tuple[str, ...]
    source_ids: tuple[str, ...]
    support_level: str
    confidence_type: str
    implementation_status: str
    verification_required: bool
    physical_action_authorized: bool
    inference_note: str
    synthetic_variation_axes: tuple[str, ...]


@dataclass(frozen=True)
class CaseLibrary:
    version: str
    cases: tuple[KnowledgeCase, ...]

    def find(
        self,
        *,
        domain: str | None = None,
        category: str | None = None,
        expected_label: str | None = None,
        source_id: str | None = None,
        implementation_status: str | None = None,
    ) -> tuple[KnowledgeCase, ...]:
        matches: list[KnowledgeCase] = []
        for item in self.cases:
            if domain is not None and item.domain != domain:
                continue
            if category is not None and item.category != category:
                continue
            if expected_label is not None and item.expected_label != expected_label:
                continue
            if source_id is not None and source_id not in item.source_ids:
                continue
            if (
                implementation_status is not None
                and item.implementation_status != implementation_status
            ):
                continue
            matches.append(item)
        return tuple(matches)

    def get(self, case_id: str) -> KnowledgeCase | None:
        for item in self.cases:
            if item.case_id == case_id:
                return item
        return None


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CaseLibraryError(f"JSON file does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CaseLibraryError(f"Unable to read valid JSON from {path}") from exc
    if not isinstance(data, dict):
        raise CaseLibraryError(f"JSON root must be an object: {path}")
    return data


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaseLibraryError(f"{field} must be a non-empty string")
    return value.strip()


def _text_tuple(value: Any, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CaseLibraryError(f"{field} must be a list")
    items = tuple(_nonempty_text(item, field) for item in value)
    if not allow_empty and not items:
        raise CaseLibraryError(f"{field} must not be empty")
    return items


def load_source_ids(registry_path: str | Path) -> frozenset[str]:
    data = _read_json_object(Path(registry_path))
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise CaseLibraryError("source registry must contain a sources list")

    ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise CaseLibraryError("each source registry entry must be an object")
        source_id = _nonempty_text(source.get("id"), "source.id")
        if source_id in ids:
            raise CaseLibraryError(f"duplicate source id: {source_id}")
        ids.add(source_id)
    if not ids:
        raise CaseLibraryError("source registry must contain at least one source")
    return frozenset(ids)


def _parse_case(raw: Any, source_ids: frozenset[str]) -> KnowledgeCase:
    if not isinstance(raw, dict):
        raise CaseLibraryError("each case must be an object")

    case_id = _nonempty_text(raw.get("case_id"), "case_id")
    sources = _text_tuple(raw.get("source_ids"), f"{case_id}.source_ids")
    unknown = sorted(set(sources) - source_ids)
    if unknown:
        raise CaseLibraryError(
            f"{case_id} references unknown source ids: {', '.join(unknown)}"
        )

    support_level = _nonempty_text(raw.get("support_level"), f"{case_id}.support_level")
    if support_level not in {"direct", "cross_reference", "governance"}:
        raise CaseLibraryError(f"{case_id} has invalid support_level")

    implementation_status = _nonempty_text(
        raw.get("implementation_status"),
        f"{case_id}.implementation_status",
    )
    if implementation_status not in {
        "runtime_supported",
        "knowledge_grounded",
        "safety_policy",
    }:
        raise CaseLibraryError(f"{case_id} has invalid implementation_status")

    verification_required = raw.get("verification_required")
    physical_action_authorized = raw.get("physical_action_authorized")
    if not isinstance(verification_required, bool):
        raise CaseLibraryError(f"{case_id}.verification_required must be boolean")
    if not isinstance(physical_action_authorized, bool):
        raise CaseLibraryError(
            f"{case_id}.physical_action_authorized must be boolean"
        )
    if physical_action_authorized:
        raise CaseLibraryError(
            f"{case_id} cannot authorize autonomous physical plant action"
        )

    return KnowledgeCase(
        case_id=case_id,
        title=_nonempty_text(raw.get("title"), f"{case_id}.title"),
        domain=_nonempty_text(raw.get("domain"), f"{case_id}.domain"),
        category=_nonempty_text(raw.get("category"), f"{case_id}.category"),
        expected_label=_nonempty_text(
            raw.get("expected_label"),
            f"{case_id}.expected_label",
        ),
        intent=_nonempty_text(raw.get("intent"), f"{case_id}.intent"),
        observed_patterns=_text_tuple(
            raw.get("observed_patterns"),
            f"{case_id}.observed_patterns",
        ),
        reasoning_basis=_text_tuple(
            raw.get("reasoning_basis"),
            f"{case_id}.reasoning_basis",
        ),
        source_ids=sources,
        support_level=support_level,
        confidence_type=_nonempty_text(
            raw.get("confidence_type"),
            f"{case_id}.confidence_type",
        ),
        implementation_status=implementation_status,
        verification_required=verification_required,
        physical_action_authorized=physical_action_authorized,
        inference_note=_nonempty_text(
            raw.get("inference_note"),
            f"{case_id}.inference_note",
        ),
        synthetic_variation_axes=_text_tuple(
            raw.get("synthetic_variation_axes"),
            f"{case_id}.synthetic_variation_axes",
            allow_empty=True,
        ),
    )


def load_case_library(
    library_path: str | Path,
    registry_path: str | Path,
) -> CaseLibrary:
    source_ids = load_source_ids(registry_path)
    data = _read_json_object(Path(library_path))

    version = _nonempty_text(data.get("library_version"), "library_version")
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise CaseLibraryError("case library must contain a non-empty cases list")

    parsed: list[KnowledgeCase] = []
    seen: set[str] = set()
    for raw in raw_cases:
        item = _parse_case(raw, source_ids)
        if item.case_id in seen:
            raise CaseLibraryError(f"duplicate case id: {item.case_id}")
        seen.add(item.case_id)
        parsed.append(item)

    declared_count = data.get("case_count")
    if declared_count != len(parsed):
        raise CaseLibraryError(
            f"case_count mismatch: declared {declared_count}, actual {len(parsed)}"
        )

    return CaseLibrary(version=version, cases=tuple(parsed))


def source_coverage(
    library: CaseLibrary,
    all_source_ids: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    used = {source for item in library.cases for source in item.source_ids}
    available = set(all_source_ids)
    return {
        "used": tuple(sorted(used)),
        "unused": tuple(sorted(available - used)),
        "unknown": tuple(sorted(used - available)),
    }
