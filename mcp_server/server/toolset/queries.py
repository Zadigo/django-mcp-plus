from collections.abc import Sequence
from typing import ClassVar

from django.db.models import Model
from django.http import HttpRequest

from mcp_server.typings import TypeDjangoMcpServer


class AbstractToolset(type):
    registry: ClassVar[dict[str, type]] = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'ModelQueryToolset':
            cls.registry[name] = cls



class ModelQueryToolset[T](metaclass=AbstractToolset):
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
    def get_exclude_fields(cls):
        pass

    @classmethod
    def get_published_models(cls):
        pass

    @classmethod
    def get_search_fields(cls):
        pass

    def get_queryset(self):
        """Returns the queryset for the model associated with this toolset. You
        can override this method to customize the queryset returned by the toolset. 
        By default, it returns all objects of the model.
        """
        if self.model is None:
            raise ValueError("ModelQueryToolset subclasses must define a model class variable.")
        return self.model._default_manager.all()
