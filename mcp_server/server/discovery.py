from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset.methods import ToolsetRegistry
from mcp_server.server.toolset.queries import (
    ModelQueryRegistry,
    _initialize_query_tools,
)


def initialize_toolsets():
    """Function to initialize the toolsets and query tools for the Django MCP server."""
    for _, cls in ToolsetRegistry.iterate_all_values():
        if cls.server is None:
            cls.server = DJANGO_MCP_SERVER

    for _, cls in ModelQueryRegistry.iterate_all_values():
        cls.server.register_mcptoolset(cls())

    _initialize_query_tools()
