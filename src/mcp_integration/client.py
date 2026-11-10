from typing import Any, cast

from mcp import Client
from mcp.server import MCPServer
from mcp.types import (
    TextResourceContents,
)


class OperationalKnowledgeClient:
    """
    AquaMind MCP client for operational
    knowledge retrieval.

    The target may be:
    - an MCPServer instance for tests/local use
    - an MCP URL for deployed use
    """

    def __init__(
        self,
        target: MCPServer | str,
    ) -> None:
        self.target = target

    async def list_documents(
        self,
    ) -> dict[str, Any]:
        """
        List documents exposed by the
        operational knowledge server.
        """

        async with Client(
            self.target,
            raise_exceptions=True,
        ) as client:

            result = await client.call_tool(
                "list_knowledge_documents",
                {},
            )

        return cast(
            dict[str, Any],
            result.structured_content,
        )

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Search operational knowledge through
        the MCP protocol.
        """

        async with Client(
            self.target,
            raise_exceptions=True,
        ) as client:

            result = await client.call_tool(
                "search_operational_knowledge",
                {
                    "query": query,
                    "limit": limit,
                },
            )

        return cast(
            dict[str, Any],
            result.structured_content,
        )

    async def read_document(
        self,
        name: str,
    ) -> str:
        """
        Read one MCP knowledge resource.
        """

        uri = (
            "knowledge://"
            f"documents/{name}"
        )

        async with Client(
            self.target,
            raise_exceptions=True,
        ) as client:

            result = (
                await client.read_resource(
                    uri
                )
            )

        content = cast(
            TextResourceContents,
            result.contents[0],
        )

        return content.text