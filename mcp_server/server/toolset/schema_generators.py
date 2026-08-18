from collections.abc import Sequence
from typing import Any

from django.db import models
from django.db.models import ForeignKey, Model, QuerySet

SCHEMA = {
    'description': '',
    '$jsonSchema': {
        'bsonType': 'object',
        'properties': {},
        'required': []
    }
}

DJANGO_TO_BSON_TYPE = {
    models.CharField: 'string',
    models.TextField: 'string',
    models.IntegerField: 'int',
    models.FloatField: 'double',
    models.BooleanField: 'bool',
    models.DateTimeField: 'date',
    models.DateField: 'date',
    models.TimeField: 'string',
    models.EmailField: 'string',
    models.URLField: 'string',
    models.DecimalField: 'double',
    models.AutoField: 'int',
    models.BigAutoField: 'long',
    models.BigIntegerField: 'long',
    models.JSONField: 'object',
}


def json_schema(model: Model, fields: list[str] | None, exclude: list[str] | None = None):
    """Generate a JSON schema for a Django model based on MongoDB's JSON schema validation. This function 
    takes a Django model class and generates a JSON schema that describes the structure of the model's fields, 
    including their types, descriptions, and any constraints such as required fields or enumerated values.
    
    Args:
        model (Model): The Django model class for which to generate the JSON schema.
        fields (list[str] | None): A list of field names to include in the schema. If None, all fields will be included.
        exclude (list[str] | None): A list of field names to exclude from the schema. If None, no fields will be excluded.
    """
    for field in model._meta.get_fields():
        logic = all(
            [
                not field.concrete,
                (fields is not None and field.name not in fields),
                (exclude is not None and field.name in exclude)
            ]
        )

        if logic:
            continue

        properties: dict[str, str] = {}

        if getattr(field, 'primary_key', False):
            properties['description'] = 'Primary unique identifier for this model'

        if isinstance(field, ForeignKey):
            properties['bsonType'] = 'objectId'
            properties['description'] = f'Foreign key to {field.related_model.__name__} model'
            properties['ref'] = field.related_model.__name__

            if field.help_text:
                properties['description'] += f' - {field.help_text}'
        else:
            for django_field, bson_type in DJANGO_TO_BSON_TYPE.items():
                if isinstance(field, django_field):
                    properties['bsonType'] = bson_type
                    break
            else:
                properties['bsonType'] = 'string'

            if field.help_text:
                properties['description'] = field.help_text

            if field.choices:
                choice_description = ', '.join(
                    [
                        f"{lhv} = {rhv}" for lhv, rhv in field.choices
                    ]
                )

                properties['enum'] = [choice[0] for choice in field.choices]

                if 'description' in properties:
                    properties['description'] += f' - {choice_description}'
                else:
                    properties['description'] = choice_description

        SCHEMA['$jsonSchema']['properties'][field.name] = properties

        logic = all(
            [
                not getattr(field, 'null', True),
                not getattr(field, 'blank', True),
            ]
        )

        if not logic:
            SCHEMA['$jsonSchema']['required'].append(field.name)

        if not SCHEMA['$jsonSchema']['required']:
            del SCHEMA['$jsonSchema']['required']

    return SCHEMA


def build_text_search_query(search_value: str, fields: Sequence[str]):
    q1 = models.Q()
    values = [value.strip().lower() for value in search_value]

    for value in values:
        q2 = models.Q()

        for field in fields:
            q2 |= models.Q(**{f"{field}__icontains": value})
        q1 &= q2
    return q1


def parse_match(matched: dict[str, str | dict[str, Any]], extended_operators, lookup_map: dict[str, str], text_search_fields = None):
    if '$and' in matched:
        return 

    if '$or' in matched:
        return

    if '$nor' in matched:
        return 

    filterfunc = models.Q()

    error_message = "Unsupported operator {operation} : review the operation syntax constraints"

    for field, condition in matched.items():
        field = translate_field(field , lookup_map)

        if isinstance(field, dict):
            for operation, value in condition.items():
                if operation.startswith('$'):
                    operation_name = operation[1:]

                    negate = False
                    if operation_name == 'ne':
                        negate = True
                        operation_name = 'eq'
                    elif operation_name == 'nin':
                        negate = True
                        operation_name = 'in'

                    if operation_name == 'eq' and value is None:
                        key = f"{field}__isnull"
                        value = True
                    elif operation_name in ['eq', 'gt', 'gte', 'lt', 'lte', 'in']:
                        final_operation = "" if operation_name=="eq" else f"__{operation_name}"
                        key = f"{field}{final_operation}"
                    elif operation_name == 'regex':
                        key = f"{field}__regex"
                    elif operation_name in extended_operators:
                        key = f"{field}__{operation_name}"
                    else:
                        raise ValueError(error_message.format_map(operation=operation_name))

                    filterfunc &= ~models.Q(**{key: value}) if negate else models.Q(**{key: value})
                else:
                    raise ValueError(error_message.format_map(operation=operation_name))
        else:
            filterfunc &= models.Q(**{field: condition})
    return filterfunc


def translate_field(field: str, lookup_map: dict[str, str]):
    if field == '_id':
        return 'pk'

    if '.' in field:
        lhv, rhv = field.split('.')
        if lhv in lookup_map:
            return f"{lookup_map[lhv]['prefix']}__{rhv}"
        else:
            raise ValueError(f"Unknown lookup alias '{lhv}', ensure it appears in the 'as' field of a previous $lookup")
    return field


def mangodb_query(queryset: QuerySet, pipeline: list[dict], allowed_models: list[type[Model]] | None = None, extended_operators: list | None = None, text_search_fields: list[str] | None = None) -> QuerySet:
    """Apply a MongoDB aggregation pipeline to a Django QuerySet. This function takes a Django QuerySet and a 
    MongoDB aggregation pipeline, and applies the pipeline to the QuerySet, returning the resulting QuerySet.
    
    Args:
        queryset (QuerySet): The Django QuerySet to which the aggregation pipeline will be applied.
        pipeline (list[dict]): A list of dictionaries representing the stages of the MongoDB aggregation pipeline.
        allowed_models (list[type[Model]] | None): An optional list of Django model classes that are allowed to be 
            used in the aggregation pipeline. If provided, any stages in the pipeline that reference models not in 
            this list will be ignored.
        extended_operators (list | None): An optional list of extended operators that can be used in the aggregation pipeline.
        text_search_fields (list[str] | None): An optional list of fields to be used for text search. If set to '*', all text fields will be used.

    Raises:
        ValueError: If the aggregation pipeline contains a $text stage and no text search fields are provided, or if the $search path contains fields that are not allowed for search.
    """
    extended_operators = extended_operators or []

    model: type[Model] = queryset.model
    
    if allowed_models is not None and text_search_fields == '*':
        _text_search_fields: list[str] = []

        for field in model._meta.get_fields():
            if field.concrete and field.is_relation:
                continue

            if not isinstance(field, (models.CharField, models.TextField)):
                continue

            _text_search_fields.append(field.name)

        text_search_fields = _text_search_fields

    lookup_alias_map = {}

    # 1. Validate the $lookup stages in the pipeline
    #  and build a lookup alias map. The lookup alias map is 
    # a dictionary that maps the 'as' field of each $lookup stage 
    # to a dictionary containing the prefix and foreign_field 
    # for that lookup. The prefix is derived from the localField 
    # of the $lookup stage, with '_id' removed if present. 
    # The foreign_field is taken directly from the $lookup stage.
    for stage in pipeline:
        if '$lookup' in stage:
            lookup = stage['$lookup']
            validate_lookup(model, lookup, allowed_models, lookup_alias_map)

            as_field = lookup['as']

            local_field = translate_field(lookup['localField'], lookup_alias_map)
            foreign_field = lookup['foreignField']
            lookup_alias_map[as_field] = {
                'prefix': local_field.replace('_id', ''),
                'foreign_field': foreign_field
            }

    # 2. 
    for i, stage in enumerate(pipeline):
        if '$match' in stage:
            match_stage = stage['$match']
            if '$text' in match_stage:
                if not text_search_fields:
                    raise ValueError("Text search fields must be provided when using $text in the $match stage.")

                search_value = match_stage['$text'].get('$search', '')
                del match_stage['$text']

                search_query = build_text_search_query(search_value, text_search_fields)

                if match_stage:
                    search_query &= parse_match(match_stage, extended_operators, lookup_alias_map, text_search_fields)

                queryset = queryset.filter(search_query)
            else:
                queryset = queryset.filter(
                    parse_match(
                        stage["$match"], 
                        extended_operators, 
                        lookup_alias_map, 
                        text_search_fields=[]
                    )
                )

        if '$search' in stage:
            search = stage['$stage']
            if not text_search_fields:
                raise ValueError("Text search fields must be provided when using $text in the $match stage.")

            search_value = search['text']['query']
            path = search['text'].get('path', text_search_fields)
            search_fields = [path] if isinstance(path, str) else path

            in_search_fields = all(
                value in text_search_fields
                    for value in search_query
            )

            if not in_search_fields:
                raise ValueError('$search path contains fields that are not allowed for search')

            query = build_text_search_query(search_value, search_fields)
            queryset = queryset.filter(query)

        if '$sort' in stage:
            order = []
            for field, direction in stage['$sort'].items():
                order.append(field if direction == 1 else f"-{field}")
            queryset = queryset.order_by(*order)

        if '$skip' in stage:
            skip_value = stage['$skip']

        if '$limit' in stage:
            queryset = queryset[:stage['$limit']]

        elif '$lookup' in stage:
            continue

    if skip_value is not None:
        queryset = queryset[skip_value:]
