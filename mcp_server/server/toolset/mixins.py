import inspect
import logging
from collections.abc import Sequence
from typing import ClassVar

from django.db.models import CharField, Model, TextField
from django.http import HttpRequest
from mcp import Tool
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset.methods import ToolsetMethodCaller
from mcp_server.typings import TypeDjangoMcpServer

logger = logging.getLogger(__name__)


class ToolsetRegistry(type):
    """A registry that tracks all the toolsets that are registered with the MCP server."""

    registry: ClassVar[dict[str, type[McpMethodsToolset]]] = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'McpMethodsToolset' and issubclass(cls, McpMethodsToolset):
            cls.registry[name] = cls

    @staticmethod
    def iterate_all_values():
        yield from ToolsetRegistry.registry.items()


class McpMethodsToolset(metaclass=ToolsetRegistry):
    """Class used as a mixin in order to let the developer define methods that 
    can be used by the MCP server. This class is meant to be subclassed and 
    extended with additional tools::

        class MyToolset(McpMethodsToolset):
            def example_tool(self):
                return "Hello, World!"

            def another_tool(self, arg1: int, arg2: int):
                return arg1 + arg2

    If your methods returns querysets, you should consider using the 
    `ModelQueryToolset` instead.
                
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this toolset is associated with. This is a class 
            variable that is shared across all instances of the toolset.
    """

    server: ClassVar[TypeDjangoMcpServer] = None

    def __init__(self, context: Context | None = None, request: HttpRequest | None = None):
        
        self.context = context
        self.request = request

        if self.server is None:
            self.server = DJANGO_MCP_SERVER

    def _add_tools_to(self, manager: ToolManager):
        """Function that iterates over all methods of the class and adds them 
        to the given ToolManager instance. This function is called by the MCP 
        server when the toolset is registered."""
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

            # If the tool has a context_kwarg, we need to wrap the method in a ToolsetMethodCaller
            tool.fn = ToolsetMethodCaller(self.__class__, name, tool.context_kwarg, forward_context=forward_context)
            # ToolsetMethodCaller is a callable that wraps 
            # the method and returns an async function that 
            # can be called by the MCP server.
            tool.is_async = True

            returned_tools.append(tool)
        return returned_tools


class ModelQueryRegistry(type):
    """A registry that tracks all the subclasses of ModelQueryToolset. This is used to keep track of 
    all the toolsets that are registered specifically with ModelQueryToolset with the MCP server.
    
    Attributes:
        registry (dict[str, ModelQueryToolset]): A dictionary that maps the name of the 
            subclass to the subclass itself. This is used to keep track of all subclasses of ModelQueryToolset
    """

    registry: ClassVar[dict[str, ModelQueryToolset]] = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'ModelQueryToolset':
            cls.registry[name] = cls

    @staticmethod
    def iterate_all_values():
        yield from ModelQueryRegistry.registry.items()


class ModelQueryToolset(metaclass=ModelQueryRegistry):
    """A class that provides a set of tools to to create tools that can 
    be used by the MCP server. This class is meant to be subclassed and 
    extended with additional tools::

        class MyToolset(ModelQueryToolset):
            model = SomeModel

            def get_queryset(self):
                return self.model.all()
                
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this toolset is associated with. This is a class 
                variable that is shared across all instances of the toolset.
        model (type[Model]): The Django model that this toolset is associated with. This is a class variable that is 
                shared across all instances of the toolset.
        exclude_fields (Sequence[str]): A sequence of field names to exclude from the query results.
        fields (Sequence[str]): A sequence of field names to include in the query results.
        search_fields (Sequence[str]): A sequence of field names to use for searching the query results.
        extra_filters (Sequence[str]): A sequence of additional filters to apply to the query results.
        extra_instructions (Sequence[str]): A sequence of additional instructions to apply to the query results.
        output_format (str): The format to use for the query results. This can be 'json', 'xml', or 'csv'.
        output_as_resource (bool): Whether to output the query results as a resource. If True, the results will be output as a resource. If False
    """

    server: ClassVar[TypeDjangoMcpServer] = None
    model: type[Model] = None
    exclude_fields: Sequence[str] = []
    fields: Sequence[str] = []
    search_fields: Sequence[str] = []
    extra_filters: Sequence[str] = []
    extra_instructions: Sequence[str] = []
    output_format: str = 'json'
    output_as_resource: bool = False

    _text_search_fields: ClassVar[set[str]] = set()
    _exclude_fields: ClassVar[set[str]] = set()
    _published_models: ClassVar[set[type[Model]]] = set()

    def __init__(self, context: Context | None = None, request: HttpRequest = None):
        self.context = context
        self.request = request

    @classmethod
    def has_model(cls):
        """Returns True if the toolset has a model defined, False otherwise."""
        return cls.model is not None

    @classmethod
    def get_exclude_fields(cls):
        if hasattr(cls, '_exclude_fields'):
            return cls._exclude_fields

        cls._exclude_fields: set[str] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._exclude_fields

        published_models = cls.get_published_models()
        for model in published_models:
            for field in model._meta.get_fields():
                if field.is_relation and field.related_model not in published_models:
                    cls._exclude_fields.add(field.name)
        return cls._exclude_fields
    
    @classmethod
    def get_published_models(cls):
        if hasattr(cls, '_published_models'):
            return cls._published_models
        
        cls._published_models: set[type[Model]] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._published_models

        for item in cls.registry.values():
            if item.server == cls.server:
                cls._published_models.add(item.model)

        return cls._published_models

    @classmethod
    def get_search_fields(cls):
        if hasattr(cls, '_text_search_fields'):
            return cls._text_search_fields

        cls._text_search_fields: set[str] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._text_search_fields
        
        if cls.search_fields:
            cls._text_search_fields: set[str] = set(cls.search_fields)
        elif not cls.fields:
            for field in cls.model._meta.get_fields():
                if not isinstance(field, (CharField, TextField)):
                    continue
                
                if field.concrete and not field.is_relation:
                    cls._text_search_fields.add(field.name)
        else:
            for field in cls.model._meta.get_fields():
                if not isinstance(field, (CharField, TextField)):
                    continue
                
                if field.name in cls.fields and field.concrete and not field.is_relation:
                    cls._text_search_fields.add(field.name)
            
        if not cls._text_search_fields:
            logger.debug(f"No text search fields found for model {cls.model.__name__}.")

        return cls._text_search_fields

    @classmethod
    def get_text_search_fields(cls):
        return []
    
    def get_queryset(self):
        """Returns the queryset for the model associated with this toolset. You
        can override this method to customize the queryset returned by the toolset. 
        By default, it returns all objects of the model.
        """
        if self.model is None:
            raise ValueError("ModelQueryToolset subclasses must define a model class variable.")
        return self.model._default_manager.all()
