import pytest
from django.db import models

from mcp_server.server.toolset.schema.mango import parse_match, translate_field

CONDITIONS = pytest.mark.parametrize(
    "testcase,condition",
    [
        (
            'not_equal',
            {
                'name': {'$ne': "Kendall"}
            }
        ),
        (
            'equal',
            {
                'name': {"$eq": "Kendall"}
            }
        ),
        (
            'not in',
            {
                'name': {"$nin": ["Kendall", "Maddie"]}
            }
        ),
        (
            'greater than',
            {
                'age': {"$gt": 30}
            }
        ),
        (
            'regex',
            {
                'name': {"$regex": ".*Kendall.*"}
            }
        ),
        (
            'extended operator',
            {
                'name': {"$contains": "Kendall"}
            }
        ),
        (
            'is null',
            {
                'name': {"$eq": None}
            }
        ),
        (
            'value not dict',
            {
                'name': "Kendall"
            }
        ),
        (
            'invalid operator',
            {
                'name': {"$invalid": "Kendall"}
            }
        ),
        (
            'with no $',
            {
                'name': {"invalid": "Kendall"}
            }
        ),
        (
            'and condition',
            {
                '$and': [
                    {'name': {"$eq": "Kendall"}},
                    {'age': {"$gt": 30}}
                ]
            }
        ),
         (
            'or condition',
            {
                '$or': [
                    {'name': {"$eq": "Kendall"}},
                    {'age': {"$gt": 30}}
                ]
            }
        ),
         (
            'nor condition',
            {
                '$nor': [
                    {'name': {"$eq": "Kendall"}},
                    {'age': {"$gt": 30}}
                ]
            }
        )
    ]
)


@CONDITIONS
def test_parse_match(testcase, condition):
    result: models.Q | None = None

    if testcase == 'invalid operator' or testcase == 'with no $':
        with pytest.raises(ValueError):
            parse_match(condition, [], {})
    else:
        if testcase != 'extended operator':
            result = parse_match(condition, [], {})
        else:
            result = parse_match(condition, ['contains'], {})

        assert isinstance(result, models.Q)



TRANSLATE = pytest.mark.parametrize(
    'testcase,field',
    [
        (
            'is _id',
            '_id'
        ),
        (
            'with "." fail',
            'user.name'
        ),
        (
            'with "." pass',
            'user.name'
        ),
        (
            'simple field',
            'name'
        ),
        (
            'with lookup map',
            'mapped_name'
        )
    ]
)

@TRANSLATE
def test_translate_field(testcase, field):
    if testcase == 'with lookup map':
        result = translate_field(field, {'user': {'prefix': 'user'}})
    elif testcase == 'with "." fail':
        with pytest.raises(ValueError):
            translate_field(field, {})
        return 
    elif testcase == 'with "." pass':
        result = translate_field(field, {'user': {'prefix': 'user'}})
    else:
        result = translate_field(field, {})

    assert isinstance(result, str)


def test_build_text_search_query():
    pass
