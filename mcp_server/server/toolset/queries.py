import logging
from collections.abc import Sequence
from typing import ClassVar

from django.db.models import CharField, Model, TextField
from django.http import HttpRequest

from mcp_server.typings import TypeDjangoMcpServer

logger = logging.getLogger(__name__)

class AbstractToolset(type):
    """A registry for all subclasses of ModelQueryToolset. This metaclass 
    is used to keep track of all subclasses of ModelQueryToolset and their associated 
    models. It also provides a way to get the published models for a given 
    server instance.
    
    Attributes:
        registry (dict[str, ModelQueryToolset]): A dictionary that maps the name of the subclass to the subclass itself. This is used to keep track of all subclasses of ModelQueryToolset
    """

    registry: ClassVar[dict[str, ModelQueryToolset]] = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'ModelQueryToolset':
            cls.registry[name] = cls



class ModelQueryToolset(metaclass=AbstractToolset):
    """A class that provides a set of tools to to create tools that can 
    be used by the MCP server. This class is meant to be subclassed and 
    extended with additional tools::

        class MyToolset(ModelQueryToolset):
            def my_tool(self):
                pass
                
    Attributes:
        server (TypeDjangoMcpServer): The MCP server instance that this toolset is associated with. This is a class 
                                      variable that is shared across all instances of the toolset.
        model (type[Model]): The Django model that this toolset is associated with. This is a class variable that is 
                             shared across all instances of the toolset.
        exclude_fields (Sequence[str]): A sequence of field names to exclude from the query results.
        fields (Sequence[str]): A sequence of field names to include in the query results.
        search_fields (Sequence[str]): A sequence of field names to use for searching the query results.
        extra_filters (Sequence[str]): A sequence of additional filters to apply to the query results.
        extra_instructions (Sequence[str]): A sequence of additional instructions to apply to the query results.
        output_format (str): The format to use for the query results. This can be 'json', 'xml', or 'csv'.
        output_as_resource (bool): Whether to output the query results as a resource. If True, the results will be output as a resource. If False
    """

    server: ClassVar[TypeDjangoMcpServer] = None
    model: type[Model] = None
    exclude_fields: Sequence[str] = []
    fields: Sequence[str] = []
    search_fields: Sequence[str] = []
    extra_filters: Sequence[str] = []
    extra_instructions: Sequence[str] = []
    output_format: str = 'json'
    output_as_resource: bool = False

    def __init__(self, context=None, request: HttpRequest = None):
        self.context = context
        self.request = request

    @classmethod
    def has_model(cls):
        """Returns True if the toolset has a model defined, False otherwise."""
        return cls.model is not None

    @classmethod
    def get_exclude_fields(cls):
        if hasattr(cls, '_exclude_fields'):
            return cls._exclude_fields

        cls._exclude_fields: set[str] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._exclude_fields

        published_models = cls.get_published_models()
        for model in published_models:
            for field in model._meta.get_fields():
                if field.is_relation and field.related_model not in published_models:
                    cls._exclude_fields.add(field.name)
        return cls._exclude_fields
    
    @classmethod
    def get_published_models(cls):
        if hasattr(cls, '_published_models'):
            return cls._published_models
        
        cls._published_models: set[type[Model]] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._published_models

        for item in cls.registry.values():
            if item.server == cls.server:
                cls._published_models.add(item.model)

        return cls._published_models

    @classmethod
    def get_search_fields(cls):
        if hasattr(cls, '_text_search_fields'):
            return cls._text_search_fields

        cls._text_search_fields: set[str] = set()
        if not cls.has_model():
            logger.warning(f"ModelQueryToolset subclass {cls.__name__} has no model defined.")
            return cls._text_search_fields
        
        if cls.search_fields is not None:
            cls._text_search_fields: set[str] = set(cls.search_fields)
        elif not cls.fields:
            for field in cls.model._meta.get_fields():
                if not isinstance(field, (CharField, TextField)):
                    continue
                
                if field.concrete and not field.is_relation:
                    cls._text_search_fields.add(field.name)
        else:
            for field in cls.model._meta.get_fields():
                if not isinstance(field, (CharField, TextField)):
                    continue
                
                if field.name in cls.fields and field.concrete and not field.is_relation:
                    cls._text_search_fields.add(field.name)
            
        if not cls._text_search_fields:
            logger.debug(f"No text search fields found for model {cls.model.__name__}.")

        return cls._text_search_fields
    
    def get_queryset(self):
        """Returns the queryset for the model associated with this toolset. You
        can override this method to customize the queryset returned by the toolset. 
        By default, it returns all objects of the model.
        """
        if self.model is None:
            raise ValueError("ModelQueryToolset subclasses must define a model class variable.")
        return self.model._default_manager.all()
