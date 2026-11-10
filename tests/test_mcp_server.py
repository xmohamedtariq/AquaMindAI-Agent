from pathlib import Path

import pytest
from mcp import Client

from src.mcp_integration.client import (
    OperationalKnowledgeClient,
)
from src.mcp_integration.server import (
    _iter_documents,
    _list_documents,
    _query_terms,
    _read_document,
    _safe_document_path,
    _search_documents,
    _snippet,
    create_mcp_server,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def knowledge_root(
    tmp_path: Path,
) -> Path:

    root = (
        tmp_path / "knowledge"
    )

    root.mkdir()

    (
        root
        / "troubleshooting.md"
    ).write_text(
        (
            "# RO Troubleshooting\n\n"
            "Biofouling may be associated "
            "with increasing pressure drop "
            "and declining permeate flow.\n\n"
            "Scaling can reduce membrane "
            "performance and may increase "
            "pressure drop."
        ),
        encoding="utf-8",
    )

    (
        root
        / "operating_principles.md"
    ).write_text(
        (
            "# Operating Principles\n\n"
            "RO recovery is related to "
            "permeate flow and feed flow.\n\n"
            "Membrane performance should "
            "be evaluated using evidence."
        ),
        encoding="utf-8",
    )

    (
        root
        / "plant_limits.json"
    ).write_text(
        (
            '{\n'
            '  "source": "demo",\n'
            '  "limits": {}\n'
            '}'
        ),
        encoding="utf-8",
    )

    (
        root
        / "ignored.csv"
    ).write_text(
        "a,b\n1,2\n",
        encoding="utf-8",
    )

    return root


def test_query_terms_normalise_and_deduplicate():
    assert (
        _query_terms(
            "Pressure FLOW pressure"
        )
        == [
            "pressure",
            "flow",
        ]
    )

    assert (
        _query_terms(
            "   !!!   "
        )
        == []
    )


def test_iter_documents(
    knowledge_root: Path,
):
    documents = (
        _iter_documents(
            knowledge_root
        )
    )

    assert [
        path.name
        for path in documents
    ] == [
        "operating_principles.md",
        "plant_limits.json",
        "troubleshooting.md",
    ]


def test_iter_documents_missing_root(
    tmp_path: Path,
):
    assert (
        _iter_documents(
            tmp_path
            / "missing"
        )
        == []
    )


def test_safe_document_path(
    knowledge_root: Path,
):
    result = (
        _safe_document_path(
            knowledge_root,
            "troubleshooting.md",
        )
    )

    assert (
        result.name
        == "troubleshooting.md"
    )


def test_safe_document_path_blocks_traversal(
    knowledge_root: Path,
):
    with pytest.raises(
        ValueError,
        match=(
            "Invalid knowledge "
            "document name"
        ),
    ):
        _safe_document_path(
            knowledge_root,
            "../secret.md",
        )

    with pytest.raises(
        ValueError,
        match=(
            "Invalid knowledge "
            "document name"
        ),
    ):
        _safe_document_path(
            knowledge_root,
            "",
        )


def test_safe_document_path_blocks_unsupported_type(
    knowledge_root: Path,
):
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported knowledge "
            "document type"
        ),
    ):
        _safe_document_path(
            knowledge_root,
            "ignored.csv",
        )


def test_safe_document_path_missing_document(
    knowledge_root: Path,
):
    with pytest.raises(
        FileNotFoundError,
        match=(
            "Knowledge document "
            "does not exist"
        ),
    ):
        _safe_document_path(
            knowledge_root,
            "missing.md",
        )


def test_read_document(
    knowledge_root: Path,
):
    path = (
        knowledge_root
        / "troubleshooting.md"
    )

    result = _read_document(
        path
    )

    assert (
        "Biofouling"
        in result
    )


def test_snippet_finds_context():
    text = (
        "A" * 200
        + " pressure drop "
        + "B" * 200
    )

    result = _snippet(
        text=text,
        terms=[
            "pressure",
        ],
    )

    assert (
        "pressure drop"
        in result
    )

    assert (
        len(result)
        < len(text)
    )


def test_list_documents(
    knowledge_root: Path,
):
    result = _list_documents(
        knowledge_root
    )

    assert result[
        "success"
    ] is True

    assert (
        result[
            "document_count"
        ]
        == 3
    )

    assert (
        result[
            "documents"
        ][0]["name"]
        == "operating_principles.md"
    )

    assert result[
        "documents"
    ][0]["uri"].startswith(
        "knowledge://documents/"
    )


def test_empty_search_query_fails(
    knowledge_root: Path,
):
    result = _search_documents(
        knowledge_root=(
            knowledge_root
        ),
        query="!!!",
    )

    assert result[
        "success"
    ] is False

    assert (
        result["matches"]
        == []
    )


def test_invalid_search_limit_fails(
    knowledge_root: Path,
):
    result = _search_documents(
        knowledge_root=(
            knowledge_root
        ),
        query="pressure",
        limit=0,
    )

    assert result[
        "success"
    ] is False

    assert (
        result["matches"]
        == []
    )


def test_search_no_match(
    knowledge_root: Path,
):
    result = _search_documents(
        knowledge_root=(
            knowledge_root
        ),
        query="nonexistentterm",
    )

    assert result[
        "success"
    ] is True

    assert (
        result[
            "match_count"
        ]
        == 0
    )

    assert (
        result["matches"]
        == []
    )


def test_search_documents_ranked_and_limited(
    knowledge_root: Path,
):
    result = _search_documents(
        knowledge_root=(
            knowledge_root
        ),
        query=(
            "pressure flow"
        ),
        limit=1,
    )

    assert result[
        "success"
    ] is True

    assert (
        result[
            "match_count"
        ]
        == 1
    )

    assert (
        result[
            "matches"
        ][0]["document"]
        == "troubleshooting.md"
    )

    assert (
        result[
            "matches"
        ][0]["score"]
        > 0
    )

    assert (
        "pressure"
        in result[
            "matches"
        ][0]["snippet"].lower()
    )


@pytest.mark.anyio
async def test_mcp_protocol_tool_discovery(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    async with Client(
        server,
        raise_exceptions=True,
    ) as client:

        result = (
            await client.list_tools()
        )

    names = {
        tool.name
        for tool in result.tools
    }

    assert (
        "list_knowledge_documents"
        in names
    )

    assert (
        "search_operational_knowledge"
        in names
    )


@pytest.mark.anyio
async def test_mcp_protocol_list_documents(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    async with Client(
        server,
        raise_exceptions=True,
    ) as client:

        result = await client.call_tool(
            "list_knowledge_documents",
            {},
        )

    assert (
        result.is_error
        is False
    )

    assert (
        result.structured_content[
            "document_count"
        ]
        == 3
    )


@pytest.mark.anyio
async def test_mcp_protocol_search(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    async with Client(
        server,
        raise_exceptions=True,
    ) as client:

        result = await client.call_tool(
            "search_operational_knowledge",
            {
                "query":
                    "biofouling pressure",
                "limit": 5,
            },
        )

    assert (
        result.is_error
        is False
    )

    assert (
        result.structured_content[
            "success"
        ]
        is True
    )

    assert (
        result.structured_content[
            "match_count"
        ]
        >= 1
    )

    assert (
        result.structured_content[
            "matches"
        ][0]["document"]
        == "troubleshooting.md"
    )


@pytest.mark.anyio
async def test_mcp_resource_discovery_and_read(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    async with Client(
        server,
        raise_exceptions=True,
    ) as client:

        templates = (
            await client
            .list_resource_templates()
        )

        uris = {
            template.uri_template
            for template
            in templates.resource_templates
        }

        assert (
            "knowledge://documents/{name}"
            in uris
        )

        result = (
            await client.read_resource(
                (
                    "knowledge://documents/"
                    "troubleshooting.md"
                )
            )
        )

    assert (
        "Biofouling"
        in result.contents[0].text
    )


@pytest.mark.anyio
async def test_operational_client_list(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    client = (
        OperationalKnowledgeClient(
            server
        )
    )

    result = (
        await client.list_documents()
    )

    assert (
        result[
            "document_count"
        ]
        == 3
    )


@pytest.mark.anyio
async def test_operational_client_search(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    client = (
        OperationalKnowledgeClient(
            server
        )
    )

    result = await client.search(
        query="scaling",
        limit=2,
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result[
            "match_count"
        ]
        == 1
    )

    assert (
        result[
            "matches"
        ][0]["document"]
        == "troubleshooting.md"
    )


@pytest.mark.anyio
async def test_operational_client_read_resource(
    knowledge_root: Path,
):
    server = create_mcp_server(
        knowledge_root
    )

    client = (
        OperationalKnowledgeClient(
            server
        )
    )

    result = (
        await client.read_document(
            "operating_principles.md"
        )
    )

    assert (
        "RO recovery"
        in result
    )