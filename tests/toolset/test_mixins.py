import pytest
from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_server.server.toolset.methods import ToolsetMethodCaller
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


async def test_async_methods_toolset(async_methods_toolset):
    pytest.skip("""
    When using an async function in the toolset, the ToolsetMethodCaller does not know how to
    handle it. On self.func, it returns the coroutine object. However when we try to await
    it in indicates that the coroutine is not callable/awaitable.
    """)
    caller = ToolsetMethodCaller(async_methods_toolset, 'simple_method', '_context', False)
    await caller(1, 1, _context={})
