from rest_framework import serializers
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.serializers import Serializer

from mcp_server.decorators import mcp_publish_create, mcp_publish_list
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


class SimpleSerializer(Serializer):
    name = serializers.CharField(max_length=100)


@mcp_publish_create
class SimpleView(CreateAPIView):
    """A simple view that creates a SimpleModel instance."""
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_list
class SimpleListView(ListAPIView):
    """A simple view that lists all SimpleModel instances."""
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer
