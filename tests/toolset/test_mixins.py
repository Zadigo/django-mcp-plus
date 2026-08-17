import pytest
from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_server.server.toolset.mixins import MCPToolset, ToolsetRegistry


@pytest.fixture
def toolset():
    class SimpleToolset(MCPToolset):
        def simple_tool(self):
            pass

    return SimpleToolset


def test_registration(toolset):
    assert len(list(ToolsetRegistry.registry.keys())) > 0


def test_add_tool_to(toolset: MCPToolset):
    instance = toolset()

    manager = ToolManager()
    instance._add_tools_to(manager)
