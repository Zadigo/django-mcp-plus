from django.db import models
from django.db.models import ForeignKey, Model

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
