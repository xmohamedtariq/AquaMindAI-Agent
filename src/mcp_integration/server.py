import re
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations


SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
}

DEFAULT_KNOWLEDGE_ROOT = Path(
    "knowledge"
)


READ_ONLY_KNOWLEDGE_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _query_terms(
    query: str,
) -> list[str]:
    """
    Normalize a search query into unique
    case-insensitive terms.
    """

    terms = re.findall(
        r"\w+",
        query.lower(),
        flags=re.UNICODE,
    )

    return list(
        dict.fromkeys(
            terms
        )
    )


def _iter_documents(
    knowledge_root: Path,
) -> list[Path]:
    """
    Return supported knowledge documents
    in deterministic order.
    """

    root = knowledge_root.resolve()

    if not root.is_dir():
        return []

    documents = [
        path
        for path in root.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    ]

    return sorted(
        documents,
        key=lambda path:
            path.name.lower(),
    )


def _safe_document_path(
    knowledge_root: Path,
    name: str,
) -> Path:
    """
    Resolve one knowledge document while
    preventing path traversal.
    """

    if (
        not name
        or "/" in name
        or "\\" in name
    ):
        raise ValueError(
            "Invalid knowledge document name."
        )

    root = knowledge_root.resolve()

    candidate = (
        root / name
    ).resolve()

    if (
        candidate.suffix.lower()
        not in SUPPORTED_EXTENSIONS
    ):
        raise ValueError(
            (
                "Unsupported knowledge "
                "document type."
            )
        )

    if not candidate.is_file():
        raise FileNotFoundError(
            (
                "Knowledge document "
                "does not exist."
            )
        )

    return candidate


def _read_document(
    path: Path,
) -> str:
    """
    Read a UTF-8 operational knowledge file.
    """

    return path.read_text(
        encoding="utf-8",
    )


def _snippet(
    text: str,
    terms: list[str],
    radius: int = 160,
) -> str:
    """
    Return a compact snippet around the
    earliest matching search term.
    """

    lowered = text.lower()

    positions = [
        position
        for term in terms
        if (
            position := lowered.find(
                term
            )
        ) >= 0
    ]

    first_match = min(
        positions
    )

    start = max(
        0,
        first_match - radius,
    )

    end = min(
        len(text),
        first_match + radius,
    )

    return (
        text[
            start:end
        ]
        .strip()
        .replace(
            "\n",
            " ",
        )
    )


def _list_documents(
    knowledge_root: Path,
) -> dict[str, Any]:
    """
    Build the structured document inventory
    returned by the MCP tool.
    """

    documents = []

    for path in _iter_documents(
        knowledge_root
    ):
        documents.append(
            {
                "name": path.name,
                "extension":
                    path.suffix.lower(),
                "size_bytes":
                    path.stat().st_size,
                "uri": (
                    "knowledge://"
                    f"documents/{path.name}"
                ),
            }
        )

    return {
        "success": True,
        "document_count": len(
            documents
        ),
        "documents": documents,
    }


def _search_documents(
    knowledge_root: Path,
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Perform deterministic lexical search over
    approved operational knowledge documents.

    This is intentionally transparent and
    reproducible for auditability.
    """

    terms = _query_terms(
        query
    )

    if not terms:
        return {
            "success": False,
            "query": query,
            "error": (
                "Search query must contain "
                "at least one searchable term."
            ),
            "matches": [],
        }

    if limit <= 0:
        return {
            "success": False,
            "query": query,
            "error": (
                "Search limit must be "
                "greater than zero."
            ),
            "matches": [],
        }

    matches: list[
        dict[str, Any]
    ] = []

    for path in _iter_documents(
        knowledge_root
    ):
        text = _read_document(
            path
        )

        lowered = text.lower()

        score = sum(
            lowered.count(
                term
            )
            for term in terms
        )

        if score <= 0:
            continue

        matches.append(
            {
                "document":
                    path.name,
                "uri": (
                    "knowledge://"
                    f"documents/{path.name}"
                ),
                "score":
                    score,
                "snippet":
                    _snippet(
                        text=text,
                        terms=terms,
                    ),
            }
        )

    matches.sort(
        key=lambda item: (
            -item["score"],
            item["document"].lower(),
        )
    )

    selected = matches[
        :limit
    ]

    return {
        "success": True,
        "query": query,
        "terms": terms,
        "match_count": len(
            selected
        ),
        "matches": selected,
        "search_method":
            "deterministic_lexical",
    }


def create_mcp_server(
    knowledge_root: str | Path = (
        DEFAULT_KNOWLEDGE_ROOT
    ),
) -> MCPServer:
    """
    Create the AquaMind operational knowledge
    MCP server.

    Exposes:
    - list_knowledge_documents
    - search_operational_knowledge
    - knowledge://documents/{name}
    """

    root = Path(
        knowledge_root
    ).resolve()

    server = MCPServer(
        "AquaMind Operational Knowledge"
    )

    @server.tool(
        annotations=READ_ONLY_KNOWLEDGE_ANNOTATIONS,
    )
    def list_knowledge_documents(
    ) -> dict[str, Any]:
        """
        List approved AquaMind operational
        knowledge documents.
        """

        return _list_documents(
            root
        )

    @server.tool(
        annotations=READ_ONLY_KNOWLEDGE_ANNOTATIONS,
    )
    def search_operational_knowledge(
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Search approved RO troubleshooting and
        operational knowledge.

        The result provides evidence snippets
        and document URIs.
        """

        return _search_documents(
            knowledge_root=root,
            query=query,
            limit=limit,
        )

    @server.resource(
        "knowledge://documents/{name}"
    )
    def read_knowledge_document(
        name: str,
    ) -> str:
        """
        Read one approved operational
        knowledge document.
        """

        path = _safe_document_path(
            knowledge_root=root,
            name=name,
        )

        return _read_document(
            path
        )

    return server


mcp = create_mcp_server()


def main() -> None:  # pragma: no cover
    """Run AquaMind MCP over stdio."""
    mcp.run(
        transport="stdio",
    )


if __name__ == "__main__":  # pragma: no cover
    main()
