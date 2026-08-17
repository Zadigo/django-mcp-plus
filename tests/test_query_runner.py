import pytest

from mcp_server.server.toolset.mixins import ModelQueryToolset
from mcp_server.server.toolset.queries import QueryRunner
from tests.testapp.models import SimpleModel


@pytest.fixture
def toolset():
    class SimpleQueryToolset(ModelQueryToolset):
        model = SimpleModel
    return SimpleQueryToolset


@pytest.mark.django_db
def test_run_query_with_existing_toolset(toolset):
    instance = QueryRunner({'simplemodel': toolset})
    result = instance.query('simplemodel')

    assert isinstance(result, list)

@pytest.mark.django_db
def test_run_query_with_none_existing_toolset(toolset):
    with pytest.raises(ValueError):
        instance = QueryRunner({'simplemodel': toolset})
        instance.query('notexists')
