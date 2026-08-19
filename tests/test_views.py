from unittest.mock import Mock, PropertyMock, patch

import pytest
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

from mcp_plus.server.base import DjangoMcpServer
from mcp_plus.server.views import (
    DrfCreateViewTool,
    DrfDeleteViewTool,
    DrfListViewTool,
    DrfUpdateViewTool,
)


@pytest.fixture
def server():
    mock_server = Mock(
        spec=DjangoMcpServer, 
        name='MockServer',
    )
    type(mock_server).name = PropertyMock(return_value='mock_server')
    return mock_server


@pytest.fixture
def request_context():
    with patch('mcp_server.server.views.DJANGO_REQUEST_CONTEXT', new=Mock()) as mock_context:
        yield mock_context


def test_drf_list_view_tool(server, request_context):
    class SimpleAPIView(ListAPIView):
        def get(self, request):
            return Response({"message": "Hello, World!"})
        
    view_tool = DrfListViewTool(server, SimpleAPIView)

    response_data = view_tool()
    assert response_data == {'message': 'Hello, World!'}


def test_drf_create_view_tool(server, request_context):
    class SimpleCreateApiView(CreateAPIView):
        def post(self, request):
            return Response({"message": "Hello, World!"})
        
    view_tool = DrfCreateViewTool(server, SimpleCreateApiView)

    response_data = view_tool({"data": {"key": "value"}})
    assert response_data == {'message': 'Hello, World!'}




def test_drf_update_view_tool(server, request_context):
    class SimpleUpdateApiView(UpdateAPIView):
        def put(self, request, *args, **kwargs):
            return Response({"message": "Hello, World!"})

    view_tool = DrfUpdateViewTool(server, SimpleUpdateApiView)

    response_data = view_tool(1, {"data": {"key": "value"}})
    assert response_data == {'message': 'Hello, World!'}




def test_drf_delete_view_tool(server, request_context):
    class SimpleDeleteApiView(DestroyAPIView):
        def delete(self, request, *args, **kwargs):
            return Response({"message": "Hello, World!"})

    view_tool = DrfDeleteViewTool(server, SimpleDeleteApiView)

    response_data = view_tool(1)
    assert response_data == {'message': 'Hello, World!'}
