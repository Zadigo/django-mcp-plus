import pytest
from django.db.models.query import QuerySet

from mcp_server.server.toolset.mixins import ModelQueryToolset
from tests.testapp.mcp import SimpleModelToolFromTestApp
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
def test_with_model_none(model_instance):
    class ModelToolsetNone(ModelQueryToolset):
        model = None

    with pytest.raises(ValueError):
        toolset = ModelToolsetNone()
        toolset.get_queryset()


@pytest.mark.django_db
def test_get_queryset(model_instance):
    toolset = SimpleModelToolFromTestApp()
    assert isinstance(toolset.get_queryset(), QuerySet)


@pytest.mark.django_db
def test_get_published_models(model_instance):
    published_models = SimpleModelToolFromTestApp.get_published_models()
    assert SimpleModel in published_models


@pytest.mark.django_db
def test_get_excluded_fields_empty(model_instance):
    excluded_fields = SimpleModelToolFromTestApp.get_exclude_fields()
    assert isinstance(excluded_fields, set)


@pytest.mark.django_db
def test_get_search_fields(model_instance):
    search_fields = SimpleModelToolFromTestApp.get_search_fields()
    assert isinstance(search_fields, set)

    # Should return the existing attribute directly
    search_fields = SimpleModelToolFromTestApp.get_search_fields()
    assert isinstance(search_fields, set)
    assert len(search_fields) > 0


@pytest.mark.django_db
def test_search_fields_with_has_no_model():
    class WithNoModel(ModelQueryToolset):
        model = None

    value = WithNoModel.get_search_fields()
    assert not WithNoModel.has_model()
    assert len(value) == 0, f'Has value: {value}'


@pytest.mark.django_db
def test_with_search_fields():
    class WithSearchFields(ModelQueryToolset):
        model = SimpleModel
        search_fields = ('name',)

    WithSearchFields.get_search_fields()

    assert len(WithSearchFields._text_search_fields) > 0
    assert isinstance(WithSearchFields._text_search_fields, set)



@pytest.mark.django_db
def test_with_fields_attribute():
    class WithFields(ModelQueryToolset):
        model = SimpleModel
        fields = ('name',)

    WithFields.get_search_fields()

    assert len(WithFields._text_search_fields) > 0
    assert isinstance(WithFields._text_search_fields, set)
