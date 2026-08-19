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
    """Main entrypoint for the Django MCP server. This class is responsible for 
    handling incoming requests and routing them to the appropriate toolset methods.

    You can use the default instance `DJANGO_MCP_SERVER` or create mutliple instances of the 
    server with different configurations.
    
    Args:
        name (str | None): The name of the server. Defaults to 'django_mcp_server'.
        instructions (str | None): Instructions for the server. Defaults to None.
        stateless (bool): Whether the server is stateless or not. Defaults to False.
    """

    def __init__(self, name: str | None = None, instructions: str | None = None, stateless: bool = False):
        # Prevent extra server settings as we do not use the embedded server
        super().__init__(name or 'django_mcp_server', instructions)
        self.stateless = stateless

        engine = import_module(settings.SESSION_ENGINE)
        self.session_store: SessionStore = engine.SessionStore

        # Add rquired tools when the the server is initialized
        server_instruction_tool = getattr(settings, 'DJANGO_MCP_PLUS_GET_SERVER_INSTRUCTIONS_TOOL', True)
        if server_instruction_tool:
            async def _get_server_instructions():
                return self.instructions or ""
            
            self._tool_manager.add_tool(
                fn=_get_server_instructions,
                name='get_server_instructions',
                description='Return MCP server instructions (if any). Always call first.'
            )

    def _handle_request(self, request: HttpRequest) -> HttpResponse:
        if not self.stateless:
            # Some requests may not have a session (e.g., when initializing 
            # a new session), so we need to handle that case.
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

            # Persist the DRF-authenticated user against this MCP session on
            # every request. Tool execution may run in a task spawned before
            # this request ever arrived (see session_auth.py), so we can't
            # rely on request.user being reachable live at call time.
            user = getattr(request, 'user', None)
            request.session['_mcp_auth_user_id'] = user.pk if user and user.is_authenticated else None

        result = async_to_sync(convert_to_starlette_request)(request, self.session_manager)
        if not self.stateless and hasattr(request, 'session'):
            request.session.save()
            result.headers[MCP_SESSION_ID_HDR] = request.session.session_key
            # Clean up the session attribute to 
            # avoid potential issues with Django's 
            # request lifecycle
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
                # Instantiate the view class to access its 
                # schema and serializer and to prevent AutoSchema
                # from raising an error when trying to access the 
                # serializer class
                view_instance = view_class(request=None, format_kwarg=None)
                schema_generator = view_class.schema
                schema_generator.view = view_instance

                func = getattr(schema_generator, 'map_serializer', None)
                if func is not None:
                    func(view_instance.get_serializer())

                # tool.parameters['properties']['body'] = schema_generator.map_serializer(
                #     view_instance.get_serializer(),  # Safer than calling serializer_class() directly
                #     # 'response'
                # )
                # view_class.schema.map_serializer(view_class().get_serializer(), 'response')
            except Exception as e:
                logger.critical(f"Could not determine body schema for {view_class.__name__} {e}. Please provide a body_schema argument.")
                raise

    def register_toolset(self, toolset: TypeToolset):
        """Register a toolset with the server. This method will add all 
        the tools defined in the toolset to the server's tool manager
        by calling the toolset's `_add_tools_to` method.
        
        Args:
            toolset (TypeToolset): The toolset class to register.
        """
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

        async def dummy(body: dict | None = None) -> list[dict]:
            """A template function that will be replaced by the actual 
            view class when the tool is called. This function will set the
            request body to the provided arguments. In other words, if
            id is provided as a required parameter, the tool will HAVE
            to be called with an id argument that will be passed to 
            the view class"""

        tool = self._tool_manager.add_tool(
            fn=dummy,
            name=name or f'{view_class.__name__}_ListTool',
            description=instructions or view_class.__doc__,
        )

        tool.fn = sync_to_async(DrfListViewTool(self, view_class, actions=actions))

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

        async def dummy(id: int, body: dict) -> dict:
            pass

        tool = self._tool_manager.add_tool(
            fn=dummy,
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

        async def dummy(body: dict) -> dict:
            pass

        tool = self._tool_manager.add_tool(
            fn=dummy,
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

        async def dummy(id: int, body: dict) -> dict:
            pass

        tool = self._tool_manager.add_tool(
            fn=dummy,
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

        async def dummy(id: int, body: dict) -> None:
            pass

        tool = self._tool_manager.add_tool(
            fn=dummy,
            name=name or f'{view_class.__name__}_DeleteTool',
            description=instructions or view_class.__doc__,
        )

        tool.fn = sync_to_async(DrfDeleteViewTool(self, view_class, actions=actions))
        self._extract_schema(tool, body_schema, view_class)


DJANGO_MCP_SERVER = DjangoMcpServer(**getattr(settings, 'DJANGO_MCP_PLUS_SERVER_CONFIG', {}))
