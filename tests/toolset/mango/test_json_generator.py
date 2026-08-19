import pytest

from mcp_plus.server.toolset.schema.json_generator import json_schema


@pytest.mark.django_db
def test_json_schema_generation(model_instance):
    values = json_schema(
        model=model_instance,
        fields=None,
        exclude=None
    )

    assert values is not None
    assert isinstance(values, dict)
    assert values == {
        'description': '',
        '$jsonSchema': {
            'bsonType': 'object',
            'properties': {
                'id': {
                    'description': 'Primary unique identifier for this model',
                    'bsonType': 'int'
                },
                'name': {
                    'bsonType': 'string'
                }
            },
            'required': ['id']
        }
    }
