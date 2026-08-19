from django.test import override_settings

from mcp_plus.server.discovery import initialize_query_tools, initialize_toolsets
from mcp_plus.server.toolset.queries import _OUTPUT_FORMATS


def test_initialize_query_tools_loading():
    initialize_query_tools()

    assert 'json' in _OUTPUT_FORMATS


def test_no_renderers():
    with override_settings(MCP_SERVER_QUERY_RENDERERS=[]):
        initialize_query_tools()

    assert 'json' in _OUTPUT_FORMATS


def test_initialize_toolsets():
    initialize_toolsets()
