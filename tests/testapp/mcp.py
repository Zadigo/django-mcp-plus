
from mcp_server.server.toolset.methods import MCPToolset


class SimpleGenericTool(MCPToolset):
    def add(self, a: int, b: int) -> list[dict]:
        return [{'result': a + b}]
