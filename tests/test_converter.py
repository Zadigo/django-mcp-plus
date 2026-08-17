from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from django.http import HttpResponse
from django.http.request import HttpRequest
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from mcp_server.server.converter import convert_to_starlette_request


@pytest.fixture
def http_request():
    return Mock(
        spec=HttpRequest,
        name='TestRequest',
        data={'key': 'value'},
        headers={'Content-Type': 'application/json'},
        method='POST',
        path='/test-path/',
        get_full_path=Mock(return_value=Mock(name='encode', return_value=b'/test-path/?query=1')),
        META={'QUERY_STRING': 'query=1', 'REMOTE_ADDR': '127.0.0.1'},
        is_secure=Mock(return_value=True),
        get_host=Mock(return_value='localhost'),
        get_port=Mock(return_value=443)
    )


@pytest.fixture
def session():
    context_manager_mock = MagicMock(name='ContextManager')
    context_manager_mock.__aenter__ = AsyncMock(
        return_value=MagicMock(
            name='HttpResponse', 
            spec=HttpRequest
        )
    )
    context_manager_mock.__aexit__ = AsyncMock(return_value=None)

    mock = MagicMock(
        spec=StreamableHTTPSessionManager,
        name='TestSessionManager',
        handle_request=AsyncMock(),
        run=MagicMock(return_value=context_manager_mock)
    )

    return mock


async def test_returns_http_request(http_request, session):
    starlette_request = await convert_to_starlette_request(http_request, session)
    assert starlette_request is not None
    assert isinstance(starlette_request, HttpResponse)


async def test_with_content_length_header(http_request, session):
    http_request.headers = {'content-length': '123'}
    starlette_request = await convert_to_starlette_request(http_request, session)
    assert starlette_request is not None
