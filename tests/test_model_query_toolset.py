import pytest
from django.db.models.query import QuerySet

from mcp_server.server.toolset.mixins import ModelQueryToolset
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
    published_models = SimpleModelToolFromTestApp.get_published_models()
    assert SimpleModel in published_models


@pytest.mark.django_db
def test_get_excluded_fields_empty(instance):
    excluded_fields = SimpleModelToolFromTestApp.get_exclude_fields()
    assert isinstance(excluded_fields, set)


@pytest.mark.django_db
def test_get_search_fields(instance):
    search_fields = SimpleModelToolFromTestApp.get_search_fields()
    assert isinstance(search_fields, set)

    # Should return the existing attribute directly
    search_fields = SimpleModelToolFromTestApp.get_search_fields()
    assert isinstance(search_fields, set)
    assert len(search_fields) > 0


@pytest.mark.django_db
def test_has_no_model():
    SimpleModelToolFromTestApp.model = None

    value = SimpleModelToolFromTestApp.get_search_fields()
    assert not value 


@pytest.mark.django_db
def test_with_search_fields():
    SimpleModelToolFromTestApp.search_fields = {'name'}
    SimpleModelToolFromTestApp.search_fields = ['name']
    SimpleModelToolFromTestApp.get_search_fields()

    assert len(SimpleModelToolFromTestApp._text_search_fields) > 0
    assert isinstance(SimpleModelToolFromTestApp._text_search_fields, set)
