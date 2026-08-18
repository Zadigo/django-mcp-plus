from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_server.server.toolset.mixins import McpMethodsToolset, ToolsetRegistry


def test_registration(methods_toolset):
    assert len(list(ToolsetRegistry.registry.keys())) > 0


def test_methods_toolset_as_mixin(methods_toolset):
    instance = methods_toolset()
    assert isinstance(instance, McpMethodsToolset)

    result = instance.simple_method(1, 2)
    assert result == [1, 2]


def test_add_tool_to(methods_toolset):
    instance = methods_toolset()

    manager = ToolManager()
    instance._add_tools_to(manager)
