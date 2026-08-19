import pytest

from mcp_plus.server.toolset.schema import mangodb_query
from mcp_plus.server.toolset.schema.old_mango import apply_json_mango_query
from tests.toolset.constants import SEARCH_PIPELINE

PIPELINES = pytest.mark.parametrize(
    "testcase,pipeline",
    [
        ('search', SEARCH_PIPELINE,)
    ]
)


@PIPELINES
@pytest.mark.django_db
def test_json_schema_generation(model_qs, testcase, pipeline):
    result = mangodb_query(
        model_qs,
        pipeline,
        allowed_models=None,
        extended_operators=None,
        text_search_fields=None
    )
    # assert result == expected


@PIPELINES
@pytest.mark.django_db
def test_old_mango_query(model_qs, testcase, pipeline):
    result = apply_json_mango_query(
        model_qs,
        pipeline,
        allowed_models=None,
        extended_operators=None,
        text_search_fields=None
    )
    # assert result == expected
