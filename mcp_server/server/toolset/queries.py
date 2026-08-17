import base64
import logging
from collections.abc import Sequence
from typing import ClassVar

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import CharField, Model, TextField
from django.http import HttpRequest
from django.utils.module_loading import import_string
from mcp.types import (
    BlobResourceContents,
    EmbeddedResource,
    TextResourceContents,
)
from mcp_types import TextContent
from rest_framework.renderers import BaseRenderer

from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset.methods import ToolManager
from mcp_server.typings import TypeDjangoMcpServer

logger = logging.getLogger(__name__)

class ModelQueryRegistry(type):
    """A registry for all subclasses of ModelQueryToolset. This metaclass 
    is used to keep track of all subclasses of ModelQueryToolset and their associated 
    models. It also provides a way to get the published models for a given 
    server instance.
    
    Attributes:
        registry (dict[str, ModelQueryToolset]): A dictionary that maps the name of the subclass to the subclass itself. This is used to keep track of all subclasses of ModelQueryToolset
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
            def my_tool(self):
                pass
                
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

    def __init__(self, context=None, request: HttpRequest = None):
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
        
        if cls.search_fields is not None:
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
    
    def get_queryset(self):
        """Returns the queryset for the model associated with this toolset. You
        can override this method to customize the queryset returned by the toolset. 
        By default, it returns all objects of the model.
        """
        if self.model is None:
            raise ValueError("ModelQueryToolset subclasses must define a model class variable.")
        return self.model._default_manager.all()


_OUTPUT_FORMATS: dict[str, BaseRenderer] = {}


class QueryRunner:
    def __init__(self, models: dict[str, ModelQueryToolset], context: dict | None = None, request: HttpRequest | None = None):
        self.query_tool_models = models
        self.context = context
        self.request = request 

    def query(self, collection: str, search_pipeline: Sequence[dict] = ()):
        """Queries the specified collection using the provided search pipeline and 
        returns the results in the specified output format.
        
        Args:
            collection (str): The collection of tools to query. This should be the name of the collection as defined in the ModelQueryToolset subclass.
            search_pipeline (Sequence[dict]): A sequence of dictionaries representing the stages of a MongoDB aggregation pipeline. 
                Each dictionary should contain the stage operator as the key and the stage parameters as the value.

        Raises:
            ValueError: If the specified collection is not available in the query tool models.
        """
        available_collections = ', '.join(str(key) for key in self.query_tool_models)

        toolset = self.query_tool_models.get(collection.lower(), None)
        if toolset is None:
            raise ValueError(f"Collection '{collection}' is not available. Available collections are: {available_collections}")

        instance = toolset(self.context, self.request)
        qs = instance.get_queryset()

        # Apply mango query 

        renderer = _OUTPUT_FORMATS.get(toolset.output_format)
        if renderer is None:
            raise ValueError(f"Output format '{toolset.output_format}' is not supported. Supported formats are: {list(_OUTPUT_FORMATS.keys())}")

        if not isinstance(renderer, BaseRenderer):
            renderer = renderer()

        _result = renderer.render(qs)

        if instance.output_as_resource:
            if not _result:
                return ['No results found']

            if  (renderer.media_type.startswith('application/') and 'json' in renderer.media_type or renderer.media_type.startswith('text/')):
                return [
                    'Results attached',
                    EmbeddedResource(
                        type='resource',
                        resource=TextResourceContents(
                            uri=f"resource://query_result/{renderer.format}",
                            mimeType=renderer.media_type,
                            text=_result
                        )
                    )
                ]
            else :
                return [
                    'Results attached',
                    EmbeddedResource(
                        type="resource",
                        resource=BlobResourceContents(
                            uri=f"resource://query_result/{renderer.format}",
                            mimeType=renderer.media_type,
                            blob=base64.b64encode(_result).decode('utf-8')
                        )
                    )
                ]
        else:
            return [
                TextContent(
                    type="text", 
                    text=_result
                )
            ]


class QueryTool:
    """A class that serves as a tool for querying data available in the server.
    
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this toolset is associated with. This is a class variable that is shared across all instances of the toolset.
        _models (dict[Model, type[ModelQueryToolset]]): A dictionary that maps the model class to the ModelQueryToolset subclass that is associated with it. This is a class variable that is shared across all instances of the toolset.
    """

    def __init__(self):
        self._models: dict[str, type[ModelQueryToolset]] = {}

    def add_model(self, query_tool: type[ModelQueryToolset]):
        if query_tool.output_format not in _OUTPUT_FORMATS:
            raise ValueError(f"Output format '{query_tool.output_format}' is not supported. Supported formats are: {list(_OUTPUT_FORMATS.keys())}")
        self._models[query_tool.model._meta.model_name] = query_tool

    def get_instructions(self):
        """Returns a string containing instructions for using the query tool. 
        The instructions include information about the available collections to query, 
        the fields that can be searched, and any extra instructions provided by the toolset."""

        template = """
        Use this tool to query data available in the server. 
        The `collection` parameter specifies the collection to query and the `search_pipeline` parameter is 
        a list of stage of a MongoDB aggregation pipeline with restricted syntax.
        
        ## Available collections to query
        """

        schema = ''

        for name, klass in self._models.items():
            template += f"""
            ### '{name}' collection [{klass.__name__}]

            ```json
            {schema}
            ```
            """

            # if klass._text_search_fields:
            #     str_fields = ', '.join(klass._text_search_fields)

            #     template += f"""
            #     #### Searchable fields

            #     {str_fields}
            #     """
            # else:
            #     template += """
            #     #### Searchable fields

            #     No searchable fields available for this collection.
            #     """

            # if klass.extra_instructions:
            #     template += f"""
            #     #### Extra instructions

            #     {klass.extra_instructions}
            #     """

        return template

    def factory(self, context, request):
        return QueryRunner()

    def _add_tools_to(self, manager: ToolManager):
        from mcp_server.server.toolset.methods import ToolsetMethodCaller
        
        def _query(collection: str, search_pipeline: list[dict] | None = None):
            pass

        name = 'query_data_collections'

        tool = manager.add_tool(
            fn=sync_to_async(_query),
            name=name,
            description=self.get_instructions()
        )

        tool.context_kwarg = '_context'
        tool.fn = ToolsetMethodCaller(self.factory, 'query', '_context', False)
        return [tool]


def _initialize_query_tools():
    """Function to initialize the query tools for the Django MCP server."""
    global _OUTPUT_FORMATS
    
    renderer_klasses: list[BaseRenderer] = []
    renderers: list[str] = getattr(settings, 'DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES', ['rest_framework.renderers.JSONRenderer'])
    for value in renderers:
        klass = import_string(value)
        renderer_klasses.append(klass)

    _OUTPUT_FORMATS = {renderer_class.format: renderer_class for renderer_class in renderer_klasses}

    server_tools: dict[TypeDjangoMcpServer, QueryTool] = {}

    for _, klass in ModelQueryRegistry.iterate_all_values():
        klass.server = klass.server or DJANGO_MCP_SERVER

        querytool = server_tools.get(klass.server)

        if querytool is None:
            querytool = QueryTool()
            server_tools[klass.server] = querytool

        querytool.add_model(klass)

    for server, tool in server_tools.items():
        server.register_toolset(tool)
