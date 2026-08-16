from importlib import import_module

from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from mcp.server import MCPServer

from mcp_server.server.converter import convert_to_starlette_request

MCP_SESSION_ID_HDR = "Mcp-Session-Id"


class DjangoMcpServer(MCPServer):
    def __init__(self, name: str | None=None, instructions: str |None=None, stateless: bool=False):
        # Prevent extra server settings as we do not use the embedded server
        super().__init__(name or 'django_mcp_server', instructions)
        self.stateless = stateless

        engine = import_module(settings.SESSION_ENGINE)
        self.session_store = engine.session_store

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
            pass

        result = async_to_sync(convert_to_starlette_request)(request, self.session_manager)
        if not self.stateless and hasattr(request, "session"):
            request.session.save()
            result.headers[MCP_SESSION_ID_HDR] = request.session.session_key
            delattr(request, "session")

        return result


DJANGO_MCP_SERVER = DjangoMcpServer()
