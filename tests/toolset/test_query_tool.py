from mcp.server.mcpserver import Context

from mcp_server.server.toolset.queries import QueryRunner, QueryTool


def test_add_model_toolset(model_query_toolset):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)

    assert len(instance._models) > 0


def test_get_instructions(model_query_toolset):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)
    result = instance.get_instructions()

    assert isinstance(result, str)
    assert "Use this tool to query data available in the server" in result


def test_factory(model_query_toolset, http_request):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)

    context = Context()
    result = instance.factory(context, http_request)

    assert isinstance(result, QueryRunner)
