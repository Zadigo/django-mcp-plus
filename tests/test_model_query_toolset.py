import pytest
from django.db.models.query import QuerySet

from mcp_server.server.toolset.queries import ModelQueryToolset
from tests.testapp.mcp import SimpleModelToolFromTestApp
from tests.testapp.models import SimpleModel


@pytest.fixture
def instance():
    return SimpleModel.objects.create(name="Test 1")


@pytest.mark.django_db
def test_with_model_none(instance):
    class ModelToolsetNone(ModelQueryToolset):
        model = None

    with pytest.raises(ValueError):
        toolset = ModelToolsetNone()
        toolset.get_queryset()


@pytest.mark.django_db
def test_get_queryset(instance):
    toolset = SimpleModelToolFromTestApp()
    assert isinstance(toolset.get_queryset(), QuerySet)


@pytest.mark.django_db
def test_get_published_models(instance):
    toolset = SimpleModelToolFromTestApp()
    published_models = toolset.get_published_models()
    assert SimpleModel in published_models


@pytest.mark.django_db
def test_get_excluded_fields_empty(instance):
    toolset = SimpleModelToolFromTestApp()
    excluded_fields = toolset.get_exclude_fields()
    assert isinstance(excluded_fields, set)


@pytest.mark.django_db
def test_get_search_fields(instance):
    toolset = SimpleModelToolFromTestApp()
    search_fields = toolset.get_search_fields()
    assert isinstance(search_fields, set)
