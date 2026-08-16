from collections.abc import Callable

from rest_framework.serializers import Serializer


def serialize(serializer: type[Serializer]):
    """A decorator that can be used to specify a serializer class 
    for a toolset method. The serializer class will be used to serialize 
    the output of the method when it is called. This decorator should be applied 
    to the method after the @toolset_method decorator::

        @serialize(MySerializer)
        def my_method(self, ...):
            ...
    """
    def wrapper(func: Callable):
        func._mcp_plus_serializer = serializer
        return func
    return wrapper
