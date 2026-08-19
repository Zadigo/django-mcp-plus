import base64
import inspect
from unittest.mock import Mock

import pydantic
import pytest
from mcp.server.mcpserver import Audio, Context, Image
from mcp.types import AudioContent, CallToolResult
from rest_framework import serializers
from rest_framework.serializers import Serializer

from mcp_plus.server.toolset.methods import (
    SyncToolsetMethodCaller,
    ToolsetMethodCaller,
)


def test_call_on_instance(model_query_toolset):
    instance = ToolsetMethodCaller(model_query_toolset, 'simple_method', '_context', forward_context=True)
    assert callable(instance)

    result = instance(_context = Context(), arg1='value1', arg2='value2')
    assert  inspect.iscoroutine(result)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'datatypes',
    [
        'list', 
        'queryset', 
        'pydantic', 
        # 'model_instance'
    ]
)
def test_sync_method_caller_without_serializer(datatypes, model_instance, model_qs):
    if datatypes == 'list':
        mock_func = Mock(
            return_value=[1, 2, 3],
            _mcp_plus_serializer=None
        )

    if datatypes == 'queryset':
        mock_func = Mock(
            return_value=model_qs,
            _mcp_plus_serializer=None
        )

    if datatypes == 'model_instance':
        mock_func = Mock(
            return_value=model_instance,
            _mcp_plus_serializer=None
        )
    
    if datatypes == 'pydantic':
        class SimpleModel(pydantic.BaseModel):
            name: str
            age: int

        mock_func = Mock(
            return_value=SimpleModel(name='John', age=30),
            _mcp_plus_serializer=None
        )


    instance = SyncToolsetMethodCaller(mock_func)
    assert callable(instance)

    result = instance()

    mock_func.assert_called_once()
    assert isinstance(result, (list, dict, pydantic.BaseModel))


@pytest.mark.parametrize(
    'datatype,value',
    [
        ('list', [{'name': 'Kendall'}]),
        ('dict', {'name': 'Kendall'})
    ]
)
def test_sync_methood_with_serializer(methods_toolset, datatype, value):
    class SimpleSerializer(Serializer):
        name = serializers.CharField()

    mock_func = Mock(
        return_value=value,
        _mcp_plus_serializer=SimpleSerializer
    )

    instance = SyncToolsetMethodCaller(mock_func)
    result = instance()

    assert isinstance(result, (list, dict))


@pytest.mark.parametrize(
    'mcptype,value',
    [
        (
            'image',
            Image('/path/to/image.jpg')
        ),
        (
            'audio',
            Audio('/path/to/audio.mp3')
        ),
        (
            'audio_content',
            CallToolResult(
                content=[
                    AudioContent(
                        type='audio', 
                        data=base64.b64encode(b'...').decode("utf-8"), 
                        mimeType="audio/wav"
                    )
                ]
            )
        )
    ]
)
def test_sync_method_with_base_mcp_responses(mcptype, value):
    mock_func = Mock(
        return_value=value,
        _mcp_plus_serializer=None
    )

    instance = SyncToolsetMethodCaller(mock_func)
    result = instance()
    assert result == value
    

