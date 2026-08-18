from mcp_server.server.toolset import McpMethodsToolset, ModelQueryToolset
from tests.testapp.models import SimpleModel


class SimpleGenericTool(McpMethodsToolset):
    def add(self, a: int, b: int) -> list[dict]:
        """Add two numbers and return the result in a list of dictionaries.

        Args:
            a (int): The first number to add.
            b (int): The second number to add.
        
        Returns:
            list[dict]: A list containing a single dictionary with the result of the addition.
        """
        return [{'result': a + b}]


class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('name')
