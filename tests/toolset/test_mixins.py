import pytest
from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_server.server.toolset.mixins import McpMethodsToolset, ToolsetRegistry


@pytest.fixture
def toolset():
    class SimpleToolset(McpMethodsToolset):
        def simple_tool(self):
            pass

    return SimpleToolset


def test_registration(toolset):
    assert len(list(ToolsetRegistry.registry.keys())) > 0


def test_add_tool_to(toolset: McpMethodsToolset):
    instance = toolset()

    manager = ToolManager()
    instance._add_tools_to(manager)
