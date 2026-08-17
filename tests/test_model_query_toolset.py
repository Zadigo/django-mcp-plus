import pytest
from django.db.models.query import QuerySet

from mcp_server.server.toolset.queries import ModelQueryToolset
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
def test_model_query_toolset():
    SimpleModel.objects.create(name="Test 1")

    class SimpleToolset(ModelQueryToolset):
        model = SimpleModel

    toolset = SimpleToolset()
    assert isinstance(toolset.get_queryset(), QuerySet)
