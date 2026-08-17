import pytest

from mcp_server.server.toolset.queries import QueryRunner


@pytest.mark.django_db
def test_run_query_with_existing_toolset(model_query_toolset):
    instance = QueryRunner({'simplemodel': model_query_toolset})
    result = instance.query('simplemodel')

    assert isinstance(result, list)


@pytest.mark.django_db
def test_run_query_with_none_existing_toolset(model_query_toolset):
    with pytest.raises(ValueError):
        instance = QueryRunner({'simplemodel': model_query_toolset})
        instance.query('notexists')
