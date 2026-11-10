import asyncio
import inspect
import importlib.metadata as metadata
from pathlib import Path

import mcp
from mcp.server import MCPServer

from src.mcp_integration.client import OperationalKnowledgeClient
from src.mcp_integration.server import create_mcp_server


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"


async def main() -> None:
    print("=== MCP PROTOCOL END-TO-END VERIFICATION ===")

    version = metadata.version("mcp")
    server_file = Path(inspect.getfile(MCPServer)).resolve()

    print(f"mcp_distribution_version={version}")
    print(f"mcp_package_file={Path(mcp.__file__).resolve()}")
    print(f"MCPServer_file={server_file}")

    if "site-packages" not in server_file.parts:
        raise RuntimeError(
            "MCPServer did not resolve from the installed MCP SDK."
        )

    server = create_mcp_server(KNOWLEDGE)

    if not isinstance(server, MCPServer):
        raise RuntimeError(
            "create_mcp_server() did not return an MCPServer instance."
        )

    print("server_instance_type=PASS")

    client = OperationalKnowledgeClient(server)

    documents = await client.list_documents()

    if documents.get("success") is not True:
        raise RuntimeError("MCP document listing failed.")

    document_count = int(
        documents.get("document_count", 0)
    )

    if document_count <= 0:
        raise RuntimeError(
            "MCP server exposed no knowledge documents."
        )

    print(f"document_count={document_count}")
    print("list_documents=PASS")

    search = await client.search(
        (
            "RO membrane scaling differential pressure "
            "permeate flow pretreatment antiscalant"
        ),
        limit=5,
    )

    if search.get("success") is not True:
        raise RuntimeError("MCP search tool failed.")

    match_count = int(
        search.get("match_count", 0)
    )

    if match_count <= 0:
        raise RuntimeError(
            "MCP search returned no evidence."
        )

    print(f"search_match_count={match_count}")
    print(
        "search_method="
        f"{search.get('search_method')}"
    )
    print("search_operational_knowledge=PASS")

    first_document = documents["documents"][0]["name"]

    content = await client.read_document(
        first_document
    )

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "MCP resource read returned empty content."
        )

    print(f"resource_document={first_document}")
    print(f"resource_characters={len(content)}")
    print("read_resource=PASS")

    print("official_sdk_resolution=PASS")
    print("mcp_protocol_end_to_end=PASS")


if __name__ == "__main__":
    asyncio.run(main())
