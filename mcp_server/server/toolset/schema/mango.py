from collections.abc import Sequence
from typing import Any

from django.db import models
from django.db.models import Model, QuerySet


def build_text_search_query(search_value: str, fields: Sequence[str]):
    q1 = models.Q()
    values = [value.strip().lower() for value in search_value]

    for value in values:
        q2 = models.Q()

        for field in fields:
            q2 |= models.Q(**{f"{field}__icontains": value})
        q1 &= q2
    return q1


def parse_match(matched: dict[str, str | dict[str, Any]], extended_operators, lookup_map: dict[str, str], text_search_fields: Sequence[str] | None = None):
    if '$and' in matched:
        return models.Q(*[
            parse_match(condition, extended_operators, lookup_map) 
                for condition in matched['$and']
            ]
        )

    if '$or' in matched:
        return models.Q(*[
                parse_match(cond, extended_operators, lookup_map)
                    for cond in matched["$or"]
            ], 
            _connector=models.Q.OR
        )

    if '$nor' in matched:
        return ~models.Q(*[
                parse_match(cond, extended_operators, lookup_map) 
                    for cond in matched["$nor"]
            ], 
            _connector=models.Q.OR
        )

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


def resolve_model_from_path(model: type[Model], field_path: str, lookup_map):
    parts = field_path.split("__")

    current_model = model
    for part in parts[:-1]:
        try:
            field = current_model._meta.get_field(part)
        except KeyError:
            raise ValueError(
                f"Invalid field path '{field_path}' at '{part}' in model '{current_model.__name__}'."
            )
        else:
            if field.is_relation:
                current_model = field.related_model
            else:
                break
        
    return current_model, parts[-1]


def interpret_projection(projection, lookup_map):
    fields: list[str] = []
    mapping = {}

    for output_field, spec in projection.items():
        if isinstance(spec, str) and spec.startswith("$"):
            path = spec[1:]

            if path == '_id':
                path = 'pk'

            internal_field = translate_field(path, lookup_map)
            fields.append(internal_field)
            mapping[output_field] = internal_field
        elif spec:
            path = output_field if output_field != '_id' else 'pk'

            internal_field = translate_field(path, lookup_map)
            fields.append(internal_field)

            mapping[output_field] = internal_field

    return fields, mapping


def postprocess_projection(queryset: QuerySet, projection_mapping: dict[str, str]):
    if not projection_mapping:
        yield from queryset
        return

    for row in queryset:
        result = {}
        for key, internal_key in projection_mapping.items():
            value = row.get(internal_key)
            assign_nested_value(result, key.split("."), value)
        yield result


def assign_nested_value(target, path_parts, value):
    for part in path_parts[:-1]:
        target = target.setdefault(part, {})
    target[path_parts[-1]] = value


def restore_field_path(field, lookup_map):
    for alias, info in lookup_map.items():
        prefix = info['prefix']
        if field.startswith(prefix + "__"):
            return alias + "." + field[len(prefix + "__"):].replace("__", ".")
    return field.replace("__", ".")


def validate_lookup(model: type[Model], lookup: dict[str, str], allowed_models, lookup_map):
    from_model_name = lookup['from']

    if allowed_models is not None and from_model_name.lower() not in allowed_models:
        raise ValueError(
            f"Invalid lookup from collection '{from_model_name}': please reveiw schemas."
        )

    local_field_name = translate_field(lookup['localField'], lookup_map)
    foreign_field_name = lookup['foreignField']

    base_model, field_name = resolve_model_from_path(model, local_field_name, lookup_map)

    try:
        local_field = base_model._meta.get_field(field_name)
    except KeyError:
        raise ValueError(
            f"Invalid localField '{lookup['localField']}': please review supported pipeline syntax and  schemas for {base_model._meta.model_name}.'."
        )

    if not local_field.is_relation or not local_field.many_to_one:
        raise ValueError(
            f"Invalid localField '{lookup['localField']}': is not a reference, please review supported pipeline syntax and  schemas for {base_model._meta.model_name}."
        )

    related_model = local_field.related_model
    if foreign_field_name != related_model._meta.pk.name and foreign_field_name != "_id" and foreign_field_name != "pk":
        raise ValueError(f"Invalid foreignField '{lookup['foreignField']}': please review supported pipeline syntax and  schemas for {base_model._meta.model_name}.")


def mangodb_query(queryset: QuerySet, pipeline: list[dict], allowed_models: list[type[Model]] | None = None, extended_operators: list | None = None, text_search_fields: list[str] | None = None) -> QuerySet:
    """Apply a MongoDB aggregation pipeline to a Django QuerySet. This function takes a Django QuerySet and a 
    MongoDB aggregation pipeline, and applies the pipeline to the QuerySet, returning the resulting QuerySet.

    ## Description

    Stages used to process a query in a MongoDB aggregation pipeline:
    
    ### Stage 1: $lookup
    
    Joins another collection:
    
    - "from" refers to a model name listed in ref in the schema (if defined)
    - "localField" refers to a field in the current model that is a foreign key to the "from" model
    - "foreignField" refers to the primary key field of the "from" model
    - "as" refers to the name of the field in the current model that will hold

    ### Stage 2: $match
    
    Filters the documents in the collection based on a specified condition.

    - Support for $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $regex in addition to $text for collections that support full text search.
    - Field references can include lookup aliases via dot notation, e.g. "user.name"

    ### Stage 3: $sort

    Sorts the documents in the collection based on a specified field and order.

    ### Stage 4: $limit

    Limits the number of documents returned by the query.

    ### Stage 5: $project

    Reshapes each document in the collection by including, excluding, or adding new fields.

    Only "flat" objects are supported and "value" is either a number/boolean to include/exclude the field or a string starting in format "$<lookupAlias>.<field>" to project a field from a previous $lookup stage.

    ### Stage 6: $search

    Performs a text search on the documents in the collection. This stage is only supported for collections that support full text search.

    ### Stage 7: $group

    Groups the documents in the collection by a specified field and applies an aggregation function to each group.

    - Must be the final stage of the pipeline.
    - Cannot include both $group and $project stages in the same pipeline.
    - `_id` can benull for global aggregation or a $<field> reference of a single field or lookup field or an object mapping "keys" to "$<field>" refs
    - Supported accumulator operators: `$sum`, `$avg`, `$min`, `$max` and `$count`

    *NOTE*: 
    
    The following stages are NOT SUPPORTED: $addFields, $set, $unset, $unwind, 
    $replaceRoot, $replaceWith, $count, $facet, $bucket, $bucketAuto, $sortByCount, $geoNear, $out, and $merge.

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

        if '$project' in stage:
            if any("$group" in value for value in pipeline[i+1:]):
                raise ValueError(
                    "$project cannot appear when pipeline contains $group :"
                    " please review pipeline syntax constriants."
                )
            projection_fields, projection_mapping = interpret_projection(stage["$project"], lookup_alias_map)

        if '$group' in stage:
            if i != len(pipeline) - 1:
                raise ValueError(
                    "$group must be the last stage in the pipeline.:"
                    " please review pipeline syntax constriants."
                )

            group: dict[str, str] = stage['$group']
            group_id = group['_id']

            annotations: dict[str, str] = {}

            for key, agg in group.items():
                if key == '_id':
                    continue

                if not isinstance(agg, dict) or len(agg) != 1:
                    raise ValueError(
                        f'Aggregation for key {key} can only be a JSON object of format '+'{"$<operator>": "<parameter>"}.'
                    )

                sub_operation, arg = next(iter(agg.items()))
                if sub_operation == '$sum':
                    if arg == 1:
                        annotations[key] = models.Count("id")
                    elif isinstance(arg, str) and arg.startswith("$"):
                        annotations[key] = models.Sum(translate_field(arg[1:], lookup_alias_map))
                    else:
                        raise ValueError("$sum only supports 1 or field references.")
                elif sub_operation == '$avg':
                    if isinstance(arg, str) and arg.startswith("$"):
                        annotations[key] = models.Avg(translate_field(arg[1:], lookup_alias_map))
                    else:
                        raise ValueError("$avg requires a field reference.")
                elif sub_operation == '$min':
                    if isinstance(arg, str) and arg.startswith("$"):
                        annotations[key] = models.Min(translate_field(arg[1:], lookup_alias_map))
                    else:
                        raise ValueError("$min requires a field reference.")
                elif sub_operation == '$max':
                    if isinstance(arg, str) and arg.startswith("$"):
                        annotations[key] = models.Max(translate_field(arg[1:], lookup_alias_map))
                    else:
                        raise ValueError("$max requires a field reference.")
                elif sub_operation == '$count':
                    if arg == 1:
                        annotations[key] = models.Count('id')
                    elif isinstance(arg, str) and arg.startswith('$'):
                        annotations[key] = models.Count(translate_field(arg[1:], lookup_alias_map))
                    else:
                        raise ValueError(
                            "$count only supports value 1 or a field reference."
                        )
                else:
                    raise ValueError(
                        f"Unsupported aggregation operator: {sub_operation}"
                    )

            if group_id is None:
                return [queryset.aggregate(**annotations)]
            elif isinstance(group_id, str) and group_id.startswith('$'):
                group_field = translate_field(group_id[1:], lookup_alias_map)
                
                mapping = {k: k for k in group if k != '_id'}
                mapping[group_id[1:]] = group_field

                return postprocess_projection(queryset.values(group_field).annotate(**annotations), mapping)
            elif isinstance(group_id, dict):
                mapping = {k: k for k in group if k != '_id'}

                group_fields = set()
                for key, formula in group_id.items():
                    if not isinstance(formula, str) or not formula.startswith('$'):
                        raise ValueError(
                            "_id in $group only supports null, string or one "
                            f"level object: value of {key} must be a string reference "
                            "to field like $<field>."
                        )
                    group_field = translate_field(formula[1:], lookup_alias_map)
                    mapping["_id."+key] = group_field
                    group_fields.add(group_field)

                return postprocess_projection(queryset.values(*group_fields).annotate(**annotations), mapping)
            else:
                raise ValueError(
                    "Unsupported _id value in $group. Only allowed: "
                    "null a \"$field\" or a {\"key\":\"$field\",...} object."
                )
        elif '$lookup' in stage:
            continue

    if skip_value is not None:
        queryset = queryset[skip_value:]

    if projection_fields:
        queryset = queryset.values(*projection_fields)
        return postprocess_projection(queryset, projection_mapping)

    return postprocess_projection(queryset.values(), None)
