from rest_framework import serializers
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.serializers import Serializer

from mcp_server.decorators import (
    mcp_publish_create,
    mcp_publish_delete,
    mcp_publish_list,
    mcp_publish_update,
    serialize,
)
from mcp_server.server.toolset.mixins import McpMethodsToolset


class MySerializer(Serializer):
    name = serializers.CharField(max_length=100)


def test_serialize_decorator():
    class SimpleToolset(McpMethodsToolset):
        @serialize(MySerializer)
        def some_tool(self):
            pass

    toolset = SimpleToolset()
    method = toolset.some_tool

    assert hasattr(method, "_mcp_plus_serializer")
    assert method._mcp_plus_serializer == MySerializer

    # "{'type': 'object', 'properties': {'name': {'type': 'string', 'maxLength': 100}}, 'required': ['name']}"


def test_mcp_publish_list_decorator():
    @mcp_publish_list
    class MyListView(ListAPIView):
        """A simple view that uses Django REST Framework's ListAPIView."""
        serializer_class = MySerializer


def test_mcp_publish_create_decorator():
    @mcp_publish_create
    class MyCreateView(CreateAPIView):
        """A simple view that uses Django REST Framework's CreateAPIView."""
        serializer_class = MySerializer



def test_mcp_publish_update_decorator():
    @mcp_publish_update
    class MyUpdateView(UpdateAPIView):
        """A simple view that uses Django REST Framework's UpdateAPIView."""
        serializer_class = MySerializer


def test_mcp_publish_delete_decorator():
    @mcp_publish_delete
    class MyDeleteView(DestroyAPIView):
        """A simple view that uses Django REST Framework's DeleteAPIView."""
        serializer_class = MySerializer
        

def test_inline_publish_decorator():
    class SimpleSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=100)

    class SimpleView(CreateAPIView):
        """A simple view that uses Django REST Framework's CreateAPIView."""
        serializer_class = SimpleSerializer

    mcp_publish_create(SimpleView)
