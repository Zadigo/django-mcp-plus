import pytest

from mcp_server.server.toolset.queries import ModelQueryToolset, QueryTool
from tests.testapp.models import SimpleModel


@pytest.fixture
def toolset():
    class SimpleQueryToolset(ModelQueryToolset):
        model = SimpleModel
    return SimpleQueryToolset


def test_add_model(toolset):
    instance = QueryTool()
    instance.add_model(toolset)

    assert len(instance._models) > 0


def test_get_instructions(toolset):
    instance = QueryTool()
    instance.add_model(toolset)
    result = instance.get_instructions()

    assert isinstance(result, str)
