import inspect
from unittest.mock import Mock

import pydantic
import pytest
from mcp.server.mcpserver import Context

from mcp_server.server.toolset.methods import (
    SyncToolsetMethodCaller,
    ToolsetMethodCaller,
)


def test_call_on_instance(model_query_toolset):
    class DummyToolset:
        def dummy_method(self, arg1, arg2):
            return [arg1, arg2]

    instance = ToolsetMethodCaller(model_query_toolset, 'simple_method', '_context', forward_context=True)
    assert callable(instance)

    result = instance(_context = Context(), arg1='value1', arg2='value2')
    assert  inspect.iscoroutine(result)


@pytest.mark.parametrize('data_types',['list', 'queryset', 'pydantic'])
@pytest.mark.django_db
def test_sync_toolset_method_caller(data_types, model_instance):
    if data_types == 'list':
        mock_func = Mock(
            return_value=[1, 2, 3],
            _mcp_plus_serializer=None
        )

    if data_types == 'queryset':
        mock_func = Mock(
            return_value=[model_instance],
            _mcp_plus_serializer=None
        )
    
    if data_types == 'pydantic':
        class SimpleModel(pydantic.BaseModel):
            name: str
            age: int

        mock_func = Mock(
            return_value=[SimpleModel],
            _mcp_plus_serializer=None
        )


    instance = SyncToolsetMethodCaller(mock_func)
    assert callable(instance)

    result = instance()

    mock_func.assert_called_once()
    assert isinstance(result, list)
