from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset.mixins import ToolsetRegistry
from mcp_server.server.toolset.queries import (
    initialize_query_tools,
)


def initialize_toolsets():
    """Function to initialize the toolsets and query tools for the Django MCP server."""
    for _, klass in ToolsetRegistry.iterate_all_values():
        if klass.server is None:
            klass.server = DJANGO_MCP_SERVER

    for _, klass in ToolsetRegistry.iterate_all_values():
        klass.server.register_toolset(klass())

    initialize_query_tools()
