from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.resources import ResourceManager
from mcp_server.server.toolset.mixins import ToolsetRegistry
from mcp_server.server.toolset.queries import (
    initialize_query_tools,
)


def initialize_toolsets():
    """Function that initializes all toolsets registered in the ToolsetRegistry. This function is
    called as early as possible in (generally in the app's AppConfig.ready() method) to ensure that all toolsets are 
    registered with the MCP server before any requests are handled.""" 
    for _, klass in ToolsetRegistry.iterate_all_values():
        if klass.server is None:
            klass.server = DJANGO_MCP_SERVER

    for _, klass in ToolsetRegistry.iterate_all_values():
        klass.server.register_toolset(klass())

    initialize_query_tools()

    ResourceManager.load_resources(DJANGO_MCP_SERVER)
