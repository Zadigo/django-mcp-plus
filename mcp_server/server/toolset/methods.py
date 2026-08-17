import contextvars
import functools
import logging
from collections.abc import Coroutine, Sequence
from types import SimpleNamespace
from typing import Any

import pydantic
from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from rest_framework.serializers import Serializer

from mcp_server.typings import TypeMcpToolset, TypeToolsetMethod

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

    def __init__(self, toolset: type[TypeMcpToolset], method_name: str, context_kwarg: str, forward_context: bool = False):
        self.toolset = toolset
        self.method_name = method_name
        self.context_kwarg = context_kwarg
        self.forward_context = forward_context

    def __call__(self, *args, **kwargs) -> Coroutine[Any, Any, list[Any]]:
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

        method = sync_to_async(SyncToolsetMethodCaller(getattr(instance, self.method_name)))
        if not self.forward_context:
            kwargs.pop(self.context_kwarg, None)

        return method(*args, **kwargs)


class SyncToolsetMethodCaller:
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
