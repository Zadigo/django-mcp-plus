from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.serializers import Serializer

from examples.mcpexample.bird_counter import serializers
from mcp_server.decorators import mcp_publish_create, mcp_publish_list


class SimpleSerializer(Serializer):
    name = serializers.CharField(max_length=100)


@mcp_publish_create
class SimpleView(CreateAPIView):
    serializer_class = SimpleSerializer


@mcp_publish_list
class SimpleListView(ListAPIView):
    serializer_class = SimpleSerializer
