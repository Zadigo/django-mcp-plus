from django.http import HttpRequest, HttpResponse
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager


async def convert_to_starlette_request(request: HttpRequest, session_manager: StreamableHTTPSessionManager) -> HttpResponse:
    pass
