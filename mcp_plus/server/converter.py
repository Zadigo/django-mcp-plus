import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.http.request import HttpRequest
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.datastructures import Headers
from starlette.types import Receive, Scope, Send


async def convert_to_starlette_request(request: HttpRequest, session_manager: StreamableHTTPSessionManager) -> HttpResponse:
    """Convert a Django HttpRequest to a Starlette request and return a Django HttpResponse.

    Args:
        request (HttpRequest): The Django HttpRequest object.
        session_manager (StreamableHTTPSessionManager): The session manager to handle the request.

    Returns:
        HttpResponse: The Django HttpResponse object.
    """
    from mcp_plus.server.toolset.methods import DJANGO_REQUEST_CONTEXT

    # TODO: Remove the DJANGO_REQUEST_CONTEXT usage 
    # and refactor to use the request object directly.
    DJANGO_REQUEST_CONTEXT.set(request)
    body = json.dumps(request.data, cls=DjangoJSONEncoder).encode('utf-8')

    headers = []

    for key, value in request.headers.items():
        if key.lower() == 'content-length':
            continue
        headers.append((key.lower().encode('latin-1'), value.encode('latin-1')))

    headers.extend([('content-length', str(len(body)).encode('latin-1'))])

    # Build ASGI scope
    scope: Scope = {
        'type': 'http',
        'http_version': '1.1',
        'method': request.method,
        'headers': headers,
        'path': request.path,
        'raw_path': request.get_full_path().encode('utf-8'),
        'query_string': request.META['QUERY_STRING'].encode('latin-1'),
        'scheme': 'https' if request.is_secure() else 'http',
        'client': (request.META.get('REMOTE_ADDR'), 0),
        'server': (request.get_host(), request.get_port()),
    }

    async def receive() -> Receive:
        return {
            'type': 'http.request',
            'body': body,
            'more_body': False,
        }

    # Prepare to collect send events
    response_started = {}
    response_body = bytearray()

    async def send(message: Send):
        if message['type'] == 'http.response.start':
            response_started['status'] = message['status']
            response_started['headers'] = Headers(raw=message['headers'])
        elif message['type'] == 'http.response.body':
            response_body.extend(message.get('body', b''))

    # Call transport
    async with session_manager.run():
        await session_manager.handle_request(scope, receive, send)

    # Build Django HttpResponse
    status = response_started.get('status', 500)
    headers = response_started.get('headers', {})

    response = HttpResponse(bytes(response_body), status=status)
    for key, value in headers.items():
        response[key] = value

    return response

