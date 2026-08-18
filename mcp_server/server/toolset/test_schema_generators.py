import pytest

from mcp_server.server.toolset.schema_generators import mangodb_query

PIPELINES = pytest.mark.parametrize(
    "pipeline",
    [
        [{"$match": {"name": {"$eq": "test"}}}],
        {'$search': {'$text': {'$search': 'test'}}},
        {'$sort': {'name': 1}},
        {'$skip': 10},
        {'$limit': 5},
        {'$lookup': {'from': 'related_model', 'localField': 'related_id', 'foreignField': 'id', 'as': 'related'}},
    ]
)


@PIPELINES
@pytest.mark.django_db
def test_json_schema_generation(model_qs, pipeline):
    result = mangodb_query(
        model_qs,
        pipeline,
        allowed_models=None,
        extended_operators=None,
        text_search_fields=None
    )
    # assert result == expected
