from mcp_server.server.toolset.mixins import MCPToolset, ModelQueryToolset
from tests.testapp.models import SimpleModel


class SimpleGenericTool(MCPToolset):
    def add(self, a: int, b: int) -> list[dict]:
        return [{'result': a + b}]


class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('name')
