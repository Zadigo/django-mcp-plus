import pytest
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.tools.tool_manager import ToolManager

from mcp_plus.server.toolset.mixins import ModelQueryToolset
from mcp_plus.server.toolset.queries import QueryRunner, QueryTool


def test_add_model_toolset(model_query_toolset):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)

    assert len(instance._models) > 0


def test_get_instructions(model_query_toolset):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)
    result = instance.get_instructions()

    assert isinstance(result, str)
    assert "Use this tool to query data available on the server" in result


def test_factory(model_query_toolset, http_request):
    instance = QueryTool()
    instance.add_model_toolset(model_query_toolset)

    context = Context()
    result = instance.factory(context, http_request)

    assert isinstance(result, QueryRunner)

@pytest.mark.parametrize(
    'testcase',
    [
        (
            'with search pipeline',
            [{'$match': {'name': 'Test 1'}}]
        ),
        # Special case: when search_pipeline is None, 
        # it should be treated as an empty list because
        # it is passed as None by Tool.run
        (
            'without search pipeline',
            None
        )
    ]
)
@pytest.mark.django_db
async def test_pass_factory_in_method_caller(model_type, testcase):
    """This test observes how the factory method on 
    the QueryTool class is called by the manager (which
    arguments are passed by the Tool.run etc.) and
    observer additional behaviours"""
    await model_type.objects.acreate(name='Test 1')
    
    class Celebrities(ModelQueryToolset):
        model = model_type

    manager = ToolManager()

    query_tool = QueryTool()
    query_tool.add_model_toolset(Celebrities)
    query_tool._add_tools_to(manager)

    _, pipeline = testcase
    result = await  manager.call_tool(
        'query_data_collections',
        arguments={
            'collection': 'simplemodel',
            'search_pipeline': pipeline if pipeline is not None else []
        },
        context=Context(),
    )

    assert result is not None
    
