import json
import sqlite3
from collections.abc import Callable
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agent.state import AgentState


DIAGNOSIS_SOURCE = "diagnose_issue"


def _failure(
    message: str,
) -> dict[str, Any]:
    """Return a standard memory-operation failure."""

    return {
        "success": False,
        "recoverable": False,
        "error": message,
    }


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return (
        datetime.now(
            timezone.utc
        )
        .replace(
            microsecond=0
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def _decode_row(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """Convert one SQLite incident row into a dictionary."""

    return {
        "incident_id":
            row["incident_id"],
        "plant_id":
            row["plant_id"],
        "created_at":
            row["created_at"],
        "diagnosis_id":
            row["diagnosis_id"],
        "severity":
            row["severity"],
        "confidence":
            row["confidence"],
        "summary":
            row["summary"],
        "evidence":
            json.loads(
                row["evidence_json"]
            ),
        "recommendations":
            json.loads(
                row[
                    "recommendations_json"
                ]
            ),
        "metadata":
            json.loads(
                row["metadata_json"]
            ),
    }


class IncidentMemory:
    """
    Persistent SQLite memory for AquaMind incidents.

    Stores evidence-backed historical incidents
    so future investigations can retrieve prior
    operational context.
    """

    def __init__(
        self,
        db_path: str | Path,
    ) -> None:

        self.db_path = Path(
            db_path
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        """Create a configured SQLite connection."""

        connection = sqlite3.connect(
            self.db_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def initialize(
        self,
    ) -> None:
        """Create the persistent incident schema."""

        with closing(
            self._connect()
        ) as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    plant_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    diagnosis_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    summary TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_incidents_plant_id
                ON incidents (plant_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_incidents_diagnosis
                ON incidents (diagnosis_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_incidents_created_at
                ON incidents (created_at)
                """
            )

            connection.commit()

    def save_incident(
        self,
        *,
        incident_id: str,
        plant_id: str,
        diagnosis_id: str,
        severity: str,
        confidence: float,
        summary: str,
        evidence: list[dict[str, Any]],
        recommendations: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Persist one incident.

        Incident IDs are unique to prevent
        accidental duplicate writes.
        """

        if not incident_id.strip():
            return _failure(
                "Incident ID is required."
            )

        if not plant_id.strip():
            return _failure(
                "Plant ID is required."
            )

        if not diagnosis_id.strip():
            return _failure(
                "Diagnosis ID is required."
            )

        try:
            confidence_value = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):
            return _failure(
                (
                    "Confidence must be "
                    "a numeric value."
                )
            )

        if (
            confidence_value < 0.0
            or confidence_value > 1.0
        ):
            return _failure(
                (
                    "Confidence must be between "
                    "0.0 and 1.0."
                )
            )

        created_at = _utc_now()

        try:
            with closing(
                self._connect()
            ) as connection:

                connection.execute(
                    """
                    INSERT INTO incidents (
                        incident_id,
                        plant_id,
                        created_at,
                        diagnosis_id,
                        severity,
                        confidence,
                        summary,
                        evidence_json,
                        recommendations_json,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        plant_id,
                        created_at,
                        diagnosis_id,
                        severity,
                        confidence_value,
                        summary,
                        json.dumps(
                            evidence,
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            recommendations,
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            metadata or {},
                            ensure_ascii=False,
                        ),
                    ),
                )

                connection.commit()

        except sqlite3.IntegrityError:
            return _failure(
                (
                    "An incident with this ID "
                    "already exists."
                )
            )

        return {
            "success": True,
            "recoverable": False,
            "incident_id":
                incident_id,
            "created_at":
                created_at,
        }

    def get_incident(
        self,
        incident_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve one incident by ID."""

        with closing(
            self._connect()
        ) as connection:

            row = connection.execute(
                """
                SELECT *
                FROM incidents
                WHERE incident_id = ?
                """,
                (
                    incident_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return _decode_row(
            row
        )

    def search_incidents(
        self,
        *,
        query: str = "",
        plant_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search historical incidents.

        Uses parameterized SQL to prevent
        SQL injection.
        """

        if limit <= 0:
            return _failure(
                (
                    "Search limit must be "
                    "greater than zero."
                )
            )

        conditions: list[str] = []
        parameters: list[Any] = []

        if plant_id:
            conditions.append(
                "plant_id = ?"
            )

            parameters.append(
                plant_id
            )

        normalized_query = (
            query.strip().lower()
        )

        if normalized_query:
            conditions.append(
                """
                (
                    LOWER(diagnosis_id) LIKE ?
                    OR LOWER(summary) LIKE ?
                )
                """
            )

            pattern = (
                f"%{normalized_query}%"
            )

            parameters.extend(
                [
                    pattern,
                    pattern,
                ]
            )

        sql = """
            SELECT *
            FROM incidents
        """

        if conditions:
            sql += (
                " WHERE "
                + " AND ".join(
                    conditions
                )
            )

        sql += """
            ORDER BY created_at DESC,
                     incident_id DESC
            LIMIT ?
        """

        parameters.append(
            limit
        )

        with closing(
            self._connect()
        ) as connection:

            rows = connection.execute(
                sql,
                parameters,
            ).fetchall()

        incidents = [
            _decode_row(
                row
            )
            for row in rows
        ]

        return {
            "success": True,
            "recoverable": False,
            "query": query,
            "plant_id": plant_id,
            "match_count": len(
                incidents
            ),
            "incidents": incidents,
        }

    def count_incidents(
        self,
    ) -> int:
        """Return the total number of stored incidents."""

        with closing(
            self._connect()
        ) as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM incidents
                """
            ).fetchone()

        return int(
            row["count"]
        )


def _latest_diagnosis(
    state: AgentState,
) -> dict[str, Any] | None:
    """
    Retrieve the latest successful diagnosis
    from agent observations.
    """

    for observation in reversed(
        state.observations
    ):

        if (
            observation.get(
                "source"
            )
            != DIAGNOSIS_SOURCE
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

        if (
            content.get(
                "success"
            )
            is not True
        ):
            continue

        return content

    return None


def search_incident_memory_from_state(
    state: AgentState,
    memory: IncidentMemory,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Search historical incidents for the
    current plant.
    """

    return memory.search_incidents(
        plant_id=state.plant_id,
        limit=limit,
    )


def save_incident_from_state(
    state: AgentState,
    memory: IncidentMemory,
    *,
    approved: bool = False,
) -> dict[str, Any]:
    """
    Persist the current diagnosis.

    Writing memory is ASK_ON_WRITE and therefore
    requires explicit human approval.
    """

    if not approved:
        return {
            "success": False,
            "recoverable": False,
            "_permission_required": True,
            "permission_level":
                "ASK_ON_WRITE",
            "message": (
                "Human approval is required "
                "before saving this incident."
            ),
        }

    diagnosis = _latest_diagnosis(
        state
    )

    if diagnosis is None:
        return _failure(
            (
                "Successful diagnosis evidence "
                "is unavailable."
            )
        )

    primary = diagnosis.get(
        "primary_hypothesis"
    )

    if not isinstance(
        primary,
        dict,
    ):
        return _failure(
            (
                "A primary diagnostic "
                "hypothesis is required."
            )
        )

    evidence = primary.get(
        "evidence"
    )

    if not isinstance(
        evidence,
        list,
    ):
        evidence = []

    recommendations = primary.get(
        "verification_steps"
    )

    if not isinstance(
        recommendations,
        list,
    ):
        recommendations = []

    incident_id = (
        f"{state.task_id}-incident"
    )

    return memory.save_incident(
        incident_id=incident_id,
        plant_id=state.plant_id,
        diagnosis_id=str(
            primary.get(
                "id",
                "unknown",
            )
        ),
        severity=str(
            primary.get(
                "severity",
                "unknown",
            )
        ),
        confidence=float(
            primary.get(
                "confidence",
                0.0,
            )
        ),
        summary=str(
            diagnosis.get(
                "conclusion",
                "",
            )
        ),
        evidence=evidence,
        recommendations=(
            recommendations
        ),
        metadata={
            "task_id":
                state.task_id,
            "source":
                "AquaMind Agent",
        },
    )


def make_search_incident_memory(
    memory: IncidentMemory,
    limit: int = 5,
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """Create the AgentLoop-compatible search tool."""

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return search_incident_memory_from_state(
            state=state,
            memory=memory,
            limit=limit,
        )

    return tool


def make_save_incident(
    memory: IncidentMemory,
    *,
    approved: bool = False,
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """Create the AgentLoop-compatible save tool."""

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return save_incident_from_state(
            state=state,
            memory=memory,
            approved=approved,
        )

    return tool