import logging
from importlib import import_module

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.contrib.sessions.backends.cache import SessionStore
from django.http import HttpRequest, HttpResponse
from mcp.server import MCPServer
from mcp.server.mcpserver.tools import Tool
from rest_framework.views import APIView

from mcp_server.server.converter import convert_to_starlette_request
from mcp_server.server.views import (
    DrfCreateViewTool,
    DrfDeleteViewTool,
    DrfListViewTool,
    DrfRetrieveViewTool,
    DrfUpdateViewTool,
)
from mcp_server.typings import TypeToolset

logger = logging.getLogger(__name__)

MCP_SESSION_ID_HDR = "Mcp-Session-Id"


class DjangoMcpServer(MCPServer):
    def __init__(self, name: str | None = None, instructions: str | None = None, stateless: bool = False):
        # Prevent extra server settings as we do not use the embedded server
        super().__init__(name or 'django_mcp_server', instructions)
        self.stateless = stateless

        engine = import_module(settings.SESSION_ENGINE)
        self.session_store: SessionStore = engine.SessionStore

        server_instruction_tool = getattr(settings, "DJANGO_MCP_GET_SERVER_INSTRUCTIONS_TOOL", True)
        if server_instruction_tool:
            async def _get_server_instructions():
                return self._mcp_server.instructions or ""
            
            self._tool_manager.add_tool(
                fn=_get_server_instructions,
                name='get_server_instructions',
                description='Return MCP server instructions (if any). Always call first.'
            )

    def _handle_request(self, request: HttpRequest) -> HttpResponse:
        if not self.stateless:
            session_key = request.headers.get(MCP_SESSION_ID_HDR)
            if session_key:
                store = self.session_store(session_key=session_key)
                if not store.exists():
                    return HttpResponse(status=404, content='Session not found')
                request.session = store
            elif request.data.get('method') == 'initialize':
                # NOTE: Trick to read body before data to avoid DRF complaining
                request.session = self.session_store()
            else:
                return HttpResponse(status=400, content="Session required for stateful server")

        result = async_to_sync(convert_to_starlette_request)(request, self.session_manager)
        if not self.stateless and hasattr(request, "session"):
            request.session.save()
            result.headers[MCP_SESSION_ID_HDR] = request.session.session_key
            # Clean up the session attribute to avoid potential issues 
            # with Django's request lifecycle
            delattr(request, 'session')

        return result

    def _check_instruction(self, instructions: str | None, view_class: type[APIView]):
        if instructions is None and view_class.__doc__ is None:
            raise ValueError("Instructions must be provided either as a decorator argument or in the view class docstring.")

    def _extract_schema(self, tool: Tool, body_schema: dict | None, view_class: type[APIView]):
        if body_schema is not None:
            tool.parameters['properties']['body'] = body_schema
        else:
            try:
                tool.parameters['properties']['body'] = view_class.schema._map_serializer(
                    view_class.serializer_class(), 
                    'response'
                )
            except AttributeError as e:
                raise logger.critical(f"Could not determine body schema for {view_class.__name__} {e}. Please provide a body_schema argument.")

            # try:
            #     tool.parameters['properties'] = view_class.schema.map_serializer(view_class.serializer_class(), 'response')
            # except Exception:
            #     try:
            #         tool.parameters['properties']['body'] = view_class.schema._map_serializer(view_class.serializer_class(), 'response')
            #     except Exception as e:
            #         raise ValueError(f"Could not determine body schema for {view_class.__name__}. Please provide a body_schema argument.") from e

    def register_toolset(self, toolset: TypeToolset):
        return toolset._add_tools_to(self._tool_manager)

    def register_drf_list_tool(self, view_class: type[APIView], name: str | None = None, instructions: str | None = None, body_schema: dict | None = None, actions: dict | None = None):
        """
        Register a Django REST Framework ListAPIView as a toolset method.

        Args:
            view_class (type): The ListAPIView class to register.
            name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
            instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
            body_schema (dict, optional): The schema of the request body. If not provided, no body schema will be set.
            actions (dict, optional): A dictionary of actions to be registered with the toolset method. If not provided, no actions will be set.
        """
        self._check_instruction(instructions, view_class)

        async def template_func(id, body: dict):
            """Template function to call the ListAPIView's get method."""

        tool = self._tool_manager.add_tool(
            fn=template_func,
            name=name or f'{view_class.__name__}_ListTool',
            description=instructions or view_class.__doc__,
        )

        # Register the view class with the toolset method using DrfListViewTool
        tool.fn = sync_to_async(DrfListViewTool(view_class))(
            self,
            view_class,
            actions=actions
        )

    def register_drf_update_tool(self, view_class: type[APIView], name: str | None = None, instructions: str | None = None, body_schema: dict | None = None, actions: dict | None = None):
        """
        Register a Django REST Framework UpdateAPIView as a toolset method.

        Args:
            view_class (type): The UpdateAPIView class to register.
            name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
            instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
            body_schema (dict, optional): The schema of the request body. If not provided, no body schema will be set.
            actions (dict, optional): DRF action mapping for viewset methods. If not provided, no actions will be set.
        """
        self._check_instruction(instructions, view_class)

        async def template_func(id, body: dict):
            pass

        tool = self._tool_manager.add_tool(
            fn=template_func,
            name=name or f'{view_class.__name__}_UpdateTool',
            description=instructions or view_class.__doc__,
        )

        # Register the view class with the toolset method using DrfUpdateViewTool
        tool.fn = sync_to_async(DrfUpdateViewTool(self, view_class, actions=actions))

        self._extract_schema(tool, body_schema, view_class)

    def register_drf_create_tool(self, view_class: type[APIView], name: str | None = None, instructions: str | None = None, body_schema: dict | None = None, actions: dict | None = None):
        """
        Register a Django REST Framework CreateAPIView as a toolset method.

        Args:
            view_class (type): The CreateAPIView class to register.
            name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
            instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
            body_schema (dict, optional): The schema of the request body. If not provided, no body schema will be set.
            actions (dict, optional): A dictionary of actions to be registered with the toolset method. If not provided, no actions will be set.
        """
        self._check_instruction(instructions, view_class)

        async def template_func(id, body: dict):
            pass

        tool = self._tool_manager.add_tool(
            fn=template_func,
            name=name or f'{view_class.__name__}_CreateTool',
            description=instructions or view_class.__doc__,
        )

        # Register the view class with the toolset method using DrfCreateViewTool
        tool.fn = sync_to_async(DrfCreateViewTool(self, view_class, actions=actions))

        self._extract_schema(tool, body_schema, view_class)

    def register_drf_retrieve_tool(self, view_class: type[APIView], name: str | None = None, instructions: str | None = None, body_schema: dict | None = None, actions: dict | None = None):
        """
        Register a Django REST Framework RetrieveAPIView as a toolset method.

        Args:
            view_class (type): The RetrieveAPIView class to register.
            name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
            instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
            body_schema (dict, optional): The schema of the request body. If not provided, no body schema will be set.
            actions (dict, optional): A dictionary of actions to be registered with the toolset method. If not provided, no actions will be set.
        """
        self._check_instruction(instructions, view_class)

        async def template_func(id, body: dict):
            pass

        tool = self._tool_manager.add_tool(
            fn=template_func,
            name=name or f'{view_class.__name__}_RetrieveTool',
            description=instructions or view_class.__doc__,
        )

        # Register the view class with the toolset method using DrfRetrieveViewTool
        tool.fn = sync_to_async(DrfRetrieveViewTool(self, view_class, actions=actions))

        self._extract_schema(tool, body_schema, view_class)

    def register_drf_delete_tool(self, view_class: type[APIView], name: str | None = None, instructions: str | None = None, body_schema: dict | None = None, actions: dict | None = None):
        """
        Register a Django REST Framework DestroyAPIView as a toolset method.

        Args:
            view_class (type): The DestroyAPIView class to register.
            name (str, optional): The name of the toolset method. If not provided, the name of the view class will be used.
            instructions (str, optional): Instructions for the toolset method. If not provided, no instructions will be set.
            body_schema (dict, optional): The schema of the request body. If not provided, no body schema will be set.
            actions (dict, optional): A dictionary of actions to be registered with the toolset method. If not provided, no actions will be set.
        """
        self._check_instruction(instructions, view_class)

        async def _template_delete(id, body: dict):
            pass

        tool = self._tool_manager.add_tool(
            fn=_template_delete,
            name=name or f'{view_class.__name__}_DeleteTool',
            description=instructions or view_class.__doc__,
        )

        # Register the view class with the toolset method using DrfDeleteViewTool
        tool.fn = sync_to_async(DrfDeleteViewTool(self, view_class, actions=actions))

        self._extract_schema(tool, body_schema, view_class)


DJANGO_MCP_SERVER = DjangoMcpServer(**getattr(settings, 'DJANGO_MCP_PLUS_SERVER_CONFIG', {}))
