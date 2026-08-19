from collections.abc import Callable

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.serializers import Serializer

from mcp_server.typings import TypeDjangoMcpServer


def serialize(serializer: type[Serializer]):
    """A decorator that can be used to specify a serializer class 
    for a toolset method. The serializer class will be used to serialize 
    the output of the method when it is called. This decorator should be applied 
    to the method after the @toolset_method decorator::

        @serialize(MySerializer)
        def my_method(self, ...):
            ...
    """
    def wrapper(func: Callable):
        func._mcp_plus_serializer = serializer
        return func
    return wrapper


def mcp_publish_create(*args: type[CreateAPIView], name: str | None = None, instructions: str | None = None, server: TypeDjangoMcpServer | None = None, actions: dict | None = None):
    """A decorator that can be used to mark a view that uses
    Django REST Framework's CreateAPIView as a view that should 
    be published to the MCP. This decorator should be applied to the 
    view class after Django REST Framework's CreateAPIView."""
    if len(args) < 1:
        raise ValueError("A view class must be provided to the mcp_publish_create decorator.")

    from mcp_server.server.base import DJANGO_MCP_SERVER

    def wrapper(view_class: type[CreateAPIView]):
        _server = server or DJANGO_MCP_SERVER
        _server.register_drf_create_tool(
            view_class,
            name=name,
            instructions=instructions,
            actions=actions,
        )
        return view_class

    if len(args) == 1 and isinstance(args[0], type):
        return wrapper(args[0])

    return wrapper


def mcp_publish_list(*args: type[ListAPIView], name: str | None = None, instructions: str | None = None, server: TypeDjangoMcpServer | None = None, actions: dict | None = None):
    """A decorator that can be used to mark a view that uses
    Django REST Framework's ListAPIView as a view that should 
    be published to the MCP. This decorator should be applied to the 
    view class after Django REST Framework's ListAPIView.

    ## Example usage

    .. code-block:: python

        @mcp_publish_list(name="My List View")
        class MyListView(ListAPIView):
            serializer_class = MySerializer

    Args:
        name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
        instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
        server (TypeDjangoMcpServer, optional): The MCP server instance to register the view with. If not provided, the default server instance will be used.
        actions (dict, optional): A dictionary of actions to be registered with the toolset method. If not provided, no actions will be set.

    Raises:
        ValueError: If no view class is provided to the decorator.
    """
    if len(args) < 1:
        raise ValueError("A view class must be provided to the mcp_publish_list decorator.")

    from mcp_server.server.base import DJANGO_MCP_SERVER

    def wrapper(view_class: type[ListAPIView]):
        _server = server or DJANGO_MCP_SERVER
        _server.register_drf_list_tool(
            view_class,
            name=name,
            instructions=instructions,
            actions=actions,
        )
        return view_class

    if len(args) == 1 and isinstance(args[0], type):
        return wrapper(args[0])

    return wrapper


def mcp_publish_update(*args: type[UpdateAPIView], name: str | None = None, instructions: str | None = None, server: TypeDjangoMcpServer | None = None, actions: dict | None = None):
    """A decorator that can be used to mark a view that uses
    Django REST Framework's UpdateAPIView as a view that should 
    be published to the MCP. This decorator should be applied to the 
    view class after Django REST Framework's UpdateAPIView."""
    if len(args) < 1:
        raise ValueError("A view class must be provided to the mcp_publish_update decorator.")

    from mcp_server.server.base import DJANGO_MCP_SERVER

    def wrapper(view_class: type[UpdateAPIView]):
        _server = server or DJANGO_MCP_SERVER
        _server.register_drf_update_tool(
            view_class,
            name=name,
            instructions=instructions,
            actions=actions,
        )
        return view_class

    if len(args) == 1 and isinstance(args[0], type):
        return wrapper(args[0])

    return wrapper


def mcp_publish_delete(*args: type[DestroyAPIView], name: str | None = None, instructions: str | None = None, server: TypeDjangoMcpServer | None = None, actions: dict | None = None):
    """A decorator that can be used to mark a view that uses
    Django REST Framework's DeleteAPIView as a view that should 
    be published to the MCP. This decorator should be applied to the 
    view class after Django REST Framework's DeleteAPIView."""
    if len(args) < 1:
        raise ValueError("A view class must be provided to the mcp_publish_delete decorator.")

    from mcp_server.server.base import DJANGO_MCP_SERVER

    def wrapper(view_class: type[DestroyAPIView]):
        _server = server or DJANGO_MCP_SERVER
        _server.register_drf_delete_tool(
            view_class,
            name=name,
            instructions=instructions,
            actions=actions,
        )
        return view_class

    if len(args) == 1 and isinstance(args[0], type):
        return wrapper(args[0])

    return wrapper
