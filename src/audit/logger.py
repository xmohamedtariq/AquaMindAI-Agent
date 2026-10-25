import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64


def _utc_now() -> str:
    """Return a UTC ISO-8601 timestamp."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_json(
    value: Any,
) -> str:
    """
    Produce deterministic JSON used for both
    persistence and cryptographic hashing.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _record_hash(
    payload: dict[str, Any],
) -> str:
    """Calculate SHA-256 for one audit payload."""

    encoded = _canonical_json(
        payload
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _integrity_result(
    *,
    valid: bool,
    event_count: int,
    error: str | None = None,
    line_number: int | None = None,
) -> dict[str, Any]:
    """Build a standardized integrity result."""

    return {
        "valid": valid,
        "event_count": event_count,
        "error": error,
        "line_number": line_number,
    }


class AuditLogger:
    """
    Append-only, hash-chained JSONL audit logger.

    AquaMind never rewrites existing audit records.
    Every new record contains the previous record hash,
    making later modification detectable.
    """

    def __init__(
        self,
        log_path: str | Path,
    ) -> None:

        self.log_path = Path(
            log_path
        )

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _last_hash(
        self,
    ) -> str:
        """
        Retrieve the latest valid record hash.

        A missing or empty log starts from GENESIS_HASH.
        """

        if (
            not self.log_path.exists()
            or self.log_path.stat().st_size == 0
        ):
            return GENESIS_HASH

        last_line: str | None = None

        with self.log_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for line in handle:
                if line.strip():
                    last_line = line

        if last_line is None:
            return GENESIS_HASH

        try:
            record = json.loads(
                last_line
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Existing audit log ends with invalid JSON."
            ) from exc

        record_hash = record.get(
            "record_hash"
        )

        if not isinstance(
            record_hash,
            str,
        ):
            raise ValueError(
                (
                    "Existing audit record does not "
                    "contain a valid record_hash."
                )
            )

        return record_hash

    def log_event(
        self,
        *,
        task_id: str,
        event_type: str,
        action: str,
        status: str,
        details: dict[str, Any] | None = None,
        actor: str = "AquaMind Agent",
        timestamp: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Append one audit event.

        Existing records are never rewritten or truncated.
        """

        if not task_id.strip():
            raise ValueError(
                "task_id is required."
            )

        if not event_type.strip():
            raise ValueError(
                "event_type is required."
            )

        if not action.strip():
            raise ValueError(
                "action is required."
            )

        if not status.strip():
            raise ValueError(
                "status is required."
            )

        normalized_details = json.loads(
            _canonical_json(
                details or {}
            )
        )

        payload: dict[str, Any] = {
            "event_id": (
                event_id
                or uuid.uuid4().hex
            ),
            "timestamp": (
                timestamp
                or _utc_now()
            ),
            "task_id":
                task_id,
            "event_type":
                event_type,
            "actor":
                actor,
            "action":
                action,
            "status":
                status,
            "details":
                normalized_details,
            "previous_hash":
                self._last_hash(),
        }

        record = {
            **payload,
            "record_hash":
                _record_hash(
                    payload
                ),
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:

            handle.write(
                _canonical_json(
                    record
                )
            )

            handle.write(
                "\n"
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        return record

    def read_events(
        self,
    ) -> list[dict[str, Any]]:
        """Read all non-empty JSONL audit records."""

        if not self.log_path.exists():
            return []

        events: list[
            dict[str, Any]
        ] = []

        with self.log_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for line in handle:
                if not line.strip():
                    continue

                events.append(
                    json.loads(
                        line
                    )
                )

        return events

    def verify_integrity(
        self,
    ) -> dict[str, Any]:
        """
        Verify the complete hash chain.

        Detects:
        - malformed JSON,
        - malformed records,
        - missing hashes,
        - broken previous-hash links,
        - modified record contents.
        """

        if not self.log_path.exists():
            return _integrity_result(
                valid=True,
                event_count=0,
            )

        expected_previous_hash = (
            GENESIS_HASH
        )

        event_count = 0

        with self.log_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for line_number, line in enumerate(
                handle,
                start=1,
            ):

                if not line.strip():
                    continue

                try:
                    record = json.loads(
                        line
                    )

                except json.JSONDecodeError:
                    return _integrity_result(
                        valid=False,
                        event_count=event_count,
                        error=(
                            "Malformed JSON audit record."
                        ),
                        line_number=line_number,
                    )

                if not isinstance(
                    record,
                    dict,
                ):
                    return _integrity_result(
                        valid=False,
                        event_count=event_count,
                        error=(
                            "Audit record must be "
                            "a JSON object."
                        ),
                        line_number=line_number,
                    )

                stored_hash = record.get(
                    "record_hash"
                )

                if not isinstance(
                    stored_hash,
                    str,
                ):
                    return _integrity_result(
                        valid=False,
                        event_count=event_count,
                        error=(
                            "Audit record is missing "
                            "a valid record_hash."
                        ),
                        line_number=line_number,
                    )

                payload = dict(
                    record
                )

                del payload[
                    "record_hash"
                ]

                if (
                    payload.get(
                        "previous_hash"
                    )
                    != expected_previous_hash
                ):
                    return _integrity_result(
                        valid=False,
                        event_count=event_count,
                        error=(
                            "Audit hash chain is broken."
                        ),
                        line_number=line_number,
                    )

                calculated_hash = (
                    _record_hash(
                        payload
                    )
                )

                if (
                    stored_hash
                    != calculated_hash
                ):
                    return _integrity_result(
                        valid=False,
                        event_count=event_count,
                        error=(
                            "Audit record contents "
                            "have been modified."
                        ),
                        line_number=line_number,
                    )

                expected_previous_hash = (
                    stored_hash
                )

                event_count += 1

        return _integrity_result(
            valid=True,
            event_count=event_count,
        )