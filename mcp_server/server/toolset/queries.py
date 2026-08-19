import base64
import logging
from collections.abc import Sequence

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.tools.tool_manager import ToolManager
from mcp.types import (
    BlobResourceContents,
    EmbeddedResource,
    TextResourceContents,
)
from mcp_types import TextContent
from rest_framework.renderers import BaseRenderer

from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset.mixins import ModelQueryRegistry
from mcp_server.server.toolset.schema.old_mango import apply_json_mango_query
from mcp_server.typings import TypeDjangoMcpServer, TypeModelQueryToolset

logger = logging.getLogger(__name__)


_OUTPUT_FORMATS: dict[str, BaseRenderer] = {}


class QueryRunner:
    """A class that serves as a runner for executing queries on the available tool models.
    It takes a dictionary of tool models and provides a method to query the specified collection
    using the provided search pipeline. The results are returned in the specified output format."""

    def __init__(self, models: dict[str, TypeModelQueryToolset], context: Context | None = None, request: HttpRequest | None = None):
        self.query_tool_models = models
        self.context = context
        self.request = request 

    def __repr__(self):
        return f"<QueryRunner models={list(self.query_tool_models.keys())}>"

    def query(self, collection: str, search_pipeline: Sequence[dict] | None = None):
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
            raise ValueError(
                f"Collection '{collection}' is not available. Available collections are: {available_collections}"
            )

        instance: TypeModelQueryToolset = toolset(self.context, self.request)
        qs = instance.get_queryset()

        # When the tool is called by Tool.run it passes additonal
        # arguments: search_pipeline and _context. search_pipeline
        # does comeback is None and this should be handled because
        # it breaks the MCP when futher down
        search_pipeline = search_pipeline or []

        # Apply mango query
        result = apply_json_mango_query(
            qs,
            search_pipeline,
            text_search_fields=instance.get_search_fields(),
            allowed_models=instance.get_published_models(),
            extended_operators=instance.extra_filters
        )

        if not result:
            if instance.output_as_resource:
                return ['No results found']
            else:
                return []

        renderer = _OUTPUT_FORMATS.get(toolset.output_format)
        if renderer is None:
            raise ValueError(f"Output format '{toolset.output_format}' is not supported. Supported formats are: {list(_OUTPUT_FORMATS.keys())}")

        if not isinstance(renderer, BaseRenderer):
            renderer = renderer()

        _result = renderer.render(result)

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
    """This class is the main default toolset for querying data collections in 
    the Django MCP server. It can be called under the `query_data_collections` 
    tool name.
    
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this 
            toolset is associated with. This is a class variable that is 
            shared across all instances of the toolset.
        _models (dict[Model, type[TypeModelQueryToolset]]): A dictionary that maps the 
            model class to the ModelQueryToolset subclass that is associated with it. This is a class 
            variable that is shared across all instances of the toolset.
    """

    def __init__(self):
        self._models: dict[str, type[TypeModelQueryToolset]] = {}

    def add_model_toolset(self, model_toolset: type[TypeModelQueryToolset]):
        if model_toolset.output_format not in _OUTPUT_FORMATS:
            raise ValueError(
                f"Output format '{model_toolset.output_format}' is not supported. "
                f"Supported formats are: {list(_OUTPUT_FORMATS.keys())}"
            )
        logger.info(f'Google Fashion {model_toolset}')
        self._models[model_toolset.model._meta.model_name] = model_toolset

    def get_instructions(self):
        """A tool used to return instructions for querying data collections."""

        template = """
        Use this tool to query data available on the server. The `collection` parameter specifies 
        the collection to query and the `search_pipeline` parameter is a list of stage of a MongoDB 
        aggregation pipeline with restricted syntax.
        
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

            if klass._text_search_fields:
                str_fields = ', '.join(klass._text_search_fields)

                template += f"""
                #### Searchable fields

                {str_fields}
                """
            else:
                template += """
                #### Searchable fields

                No searchable fields available for this collection.
                """

            if klass.extra_instructions:
                template += f"""
                #### Extra instructions

                {klass.extra_instructions}
                """

        return template

    def factory(self, context: Context, request: HttpRequest):
        return QueryRunner(self._models, context=context, request=request)

    def _add_tools_to(self, manager: ToolManager):
        from mcp_server.server.toolset.methods import ToolsetMethodCaller
        
        def dummy(collection: str, search_pipeline: list[dict] | None = None):
            pass

        name = 'query_data_collections'

        tool = manager.add_tool(
            fn=sync_to_async(dummy),
            name=name,
            description=self.get_instructions()
        )

        tool.context_kwarg = '_context'
        tool.fn = ToolsetMethodCaller(self.factory, 'query', '_context', False)
        # Mark the tool as asynchronous to indicate 
        # that it should be executed in an 
        # asynchronous context since ToolsetMethodCaller 
        # is an async callable.
        tool.is_async = True
        return [tool]


def initialize_query_tools():
    """Specific function used to register ModelQueryToolset subclasses to the Django MCP server. 
    This function is called during the server initialization process to ensure that all 
    available query tools are properly registered and ready for use."""
    global _OUTPUT_FORMATS
    
    renderer_klasses: list[BaseRenderer] = []
    user_provided_renderers: list[str] = getattr(settings, 'DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES', [])

    json_renderer = 'rest_framework.renderers.JSONRenderer'

    if not user_provided_renderers:
        user_provided_renderers.extend([json_renderer])

    # At least ensure that the JSON renderer is always 
    # included in the list of renderers since MCP servers
    # are expected to support JSON output by default.
    if json_renderer not in user_provided_renderers:
        user_provided_renderers.append(json_renderer)

    for value in user_provided_renderers:
        klass = import_string(value)
        renderer_klasses.append(klass)

    _OUTPUT_FORMATS = {
        renderer_class.format: renderer_class 
            for renderer_class in renderer_klasses
    }

    server_tools: dict[TypeDjangoMcpServer, QueryTool] = {}

    for _, klass in ModelQueryRegistry.iterate_all_values():
        klass.server = klass.server or DJANGO_MCP_SERVER

        querytool = server_tools.get(klass.server)

        # Attach the query tool to the 
        # server if it doesn't already exist
        if querytool is None:
            querytool = QueryTool()
            server_tools[klass.server] = querytool

        querytool.add_model_toolset(klass)

    for server, toolset in server_tools.items():
        server.register_toolset(toolset)
