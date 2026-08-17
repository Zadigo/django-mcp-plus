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
from mcp_server.server.toolset.methods import MCPToolset


class MySerializer(Serializer):
    name = serializers.CharField(max_length=100)


def test_serialize_decorator():
    class SimpleToolset(MCPToolset):
        @serialize(MySerializer)
        def some_tool(self):
            pass

    toolset = SimpleToolset()
    method = toolset.some_tool

    assert hasattr(method, "_mcp_plus_serializer")
    assert method._mcp_plus_serializer == MySerializer


def test_mcp_publish_list_decorator():
    @mcp_publish_list
    class MyListView(ListAPIView):
        """A simple view that uses Django REST Framework's ListAPIView."""
        serializer_class = MySerializer

    assert hasattr(MyListView, "_mcp_plus_toolset_method")
    assert MyListView._mcp_plus_toolset_method["name"] == "MyListView"
    assert MyListView._mcp_plus_toolset_method["instructions"] is None
    assert MyListView._mcp_plus_toolset_method["actions"] is None


def test_mcp_publish_create_decorator():
    @mcp_publish_create
    class MyCreateView(CreateAPIView):
        """A simple view that uses Django REST Framework's CreateAPIView."""
        serializer_class = MySerializer

    assert hasattr(MyCreateView, "_mcp_plus_toolset_method")
    assert MyCreateView._mcp_plus_toolset_method["name"] == "MyCreateView"
    assert MyCreateView._mcp_plus_toolset_method["instructions"] is None
    assert MyCreateView._mcp_plus_toolset_method["actions"] is None



def test_mcp_publish_update_decorator():
    @mcp_publish_update
    class MyUpdateView(UpdateAPIView):
        """A simple view that uses Django REST Framework's UpdateAPIView."""
        serializer_class = MySerializer

    assert hasattr(MyUpdateView, "_mcp_plus_toolset_method")
    assert MyUpdateView._mcp_plus_toolset_method["name"] == "MyUpdateView"
    assert MyUpdateView._mcp_plus_toolset_method["instructions"] is None
    assert MyUpdateView._mcp_plus_toolset_method["actions"] is None



def test_mcp_publish_delete_decorator():
    @mcp_publish_delete
    class MyDeleteView(DestroyAPIView):
        """A simple view that uses Django REST Framework's DeleteAPIView."""
        
    assert hasattr(MyDeleteView, "_mcp_plus_toolset_method")
    assert MyDeleteView._mcp_plus_toolset_method["name"] == "MyDeleteView"
    assert MyDeleteView._mcp_plus_toolset_method["instructions"] is None
    assert MyDeleteView._mcp_plus_toolset_method["actions"] is None


def test_inline_publish_decorator():
    class SimpleSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=100)

    class SimpleView(CreateAPIView):
        """A simple view that uses Django REST Framework's CreateAPIView."""
        serializer_class = SimpleSerializer

    mcp_publish_create(SimpleView)
