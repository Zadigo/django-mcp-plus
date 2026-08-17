import contextvars
import functools
import inspect
import logging
from collections.abc import Sequence
from types import SimpleNamespace
from typing import ClassVar

import pydantic
from django.db.models import QuerySet
from mcp import Tool
from mcp.server.mcpserver.tools.tool_manager import ToolManager
from rest_framework.serializers import Serializer

from mcp_server.typings import TypeDjangoMcpServer, TypeToolsetMethod

logger = logging.getLogger(__name__)

# Context variable to store the current Django request object. This variable is 
# used to pass the request object to the toolset methods when they are called. 
# The request object is stored in a context variable so that it can be accessed 
# from anywhere in the code, even if the method is called from a different 
# thread or context.
DJANGO_REQUEST_CONTEXT = contextvars.ContextVar('django_request')

class ToolsetMethodCaller:
    """A class that provides a way to call methods on a toolset instance. This class is used to wrap the methods of a toolset
    instance so that they can be called with the correct context and request objects. This class is meant to be used
    internally by the MCP server and should not be instantiated directly.

    Attributes:
        toolset (MCPToolset): The toolset instance that this method caller is associated with.
        method (str): The name of the method that this method caller is associated with.
        context_kwarg (str): The name of the keyword argument that will be used to pass the context object to the method.
        forward_context (bool): A boolean indicating whether the context object should be forwarded to the method. If True, the context object will be passed to the method as the keyword argument specified by context_kwarg.
    """

    def __init__(self, toolset: type[MCPToolset], method_name: str, context_kwarg: str, forward_context: bool = False):
        self.toolset = toolset
        self.method_name = method_name
        self.context_kwarg = context_kwarg
        self.forward_context = forward_context

    def __call__(self, *args, **kwargs):
        # Create an instance of the toolset class, passing in the context 
        # and request objects as keyword arguments. The context object is 
        # retrieved from the kwargs dictionary using the context_kwarg attribute, 
        # and the request object is retrieved from the DJANGO_REQUEST_CONTEXT 
        # context variable. If the context_kwarg attribute is not present in the
        #  kwargs dictionary, a KeyError will be raised.
        instance = self.toolset(
            context=kwargs[self.context_kwarg],
            request=DJANGO_REQUEST_CONTEXT.get(SimpleNamespace())
        )

        method = getattr(instance, self.method_name)


class SyncToolMethodCaller:
    def __init__(self, func: TypeToolsetMethod):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        try:
            result = self.func(*args, **kwargs)
        except Exception as e:
            # Handle the exception as needed, for example, log it or re-raise it
            raise e
        else:
            values: list = []
            if isinstance(result, QuerySet):
                values = list(result)
            elif isinstance(result, pydantic.BaseModel):
                values = result.model_dump()
            elif isinstance(result, Sequence) and all(isinstance(item, pydantic.BaseModel) for item in result):
                values = [item.model_dump() for item in result]

            serializer_class = getattr(self.func, '_mcp_plus_serializer', None)
            if serializer_class is not None:
                many = isinstance(values, list)

                serializer: Serializer = serializer_class(data=values, many=many)
                serializer.is_valid(raise_exception=True)

                values = serializer.data
            return values


class AbstractToolset(type):
    registry: ClassVar[dict[str, type]] = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'MCPToolset' and issubclass(cls, MCPToolset):
            cls.registry[name] = cls


class MCPToolset(metaclass=AbstractToolset):
    """A class that provides a set of tools to to create tools that can 
    be used by the MCP server. This class is meant to be subclassed and 
    extended with additional tools::

        class MyToolset(MCPToolset):
            def my_tool(self):
                pass
                
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this toolset is associated with. This is a class 
                                      variable that is shared across all instances of the toolset.
    """

    server: ClassVar[TypeDjangoMcpServer] = None

    def __init__(self, context = None, request = None):
        from mcp_server.server.base import DJANGO_MCP_SERVER
        
        self.context = context
        self.request = request

        if self.server is None:
            self.server = DJANGO_MCP_SERVER

    def _add_tools(self, manager: ToolManager):
        returned_tools: list[Tool] = []

        values = inspect.getmembers(self, predicate=inspect.ismethod)

        for name, method in values:
            if not callable(method) or name.startswith('_'):
                continue

            forward_context = False

            tool = manager.add_tool(fn=method, name=name, description=method.__doc__)
            if tool.context_kwarg is None:
                tool.context_kwarg = '_context'
            else:
                forward_context = True

            tool.fn = ToolsetMethodCaller(self.__class__, name, tool.context_kwarg, forward_context=forward_context)
            returned_tools.append(tool)
        return returned_tools

