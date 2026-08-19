import json
import logging

import httpx2
import pandas
import pydantic
from django.core.cache import cache
from mcp_types import Completion, CompletionArgument, CompletionContext, PromptReference
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from pydantic import BaseModel
from rest_framework import fields, serializers
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.serializers import Serializer

from mcp_server.decorators import mcp_publish_create, mcp_publish_list, serialize
from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset import McpMethodsToolset, ModelQueryToolset
from tests.testapp.models import SimpleModel

logger = logging.getLogger(__name__)

class ParkingModel(BaseModel):
    nb_places: int | None = None
    gratuit: str | None = None
    type_usagers: str | None = None

    @pydantic.field_validator('gratuit')
    @classmethod
    def validate_gratuit(cls, value):
        if isinstance(value, str):
            return value == 'true'
        return False


class ParkingSerializer(Serializer):
    nb_places = fields.IntegerField(required=False, allow_null=True)
    gratuit = fields.BooleanField(required=False, allow_null=True)
    type_usagers = fields.CharField(required=False, allow_null=True)
    

class SimpleGenericTool(McpMethodsToolset):
    def _get_dataset(self):
        url = 'https://hub.huwise.com/api/explore/v2.1/catalog/datasets/osm-france-parking-area/records/?lang=fr&limit=10&offset=0'
        data = cache.get('test_data', None)
        if data is None:
            with httpx2.Client() as client:
                response = client.get(url)
                results = response.json()['results']

                df = pandas.DataFrame(results)
                df = df[['nb_places', 'gratuit', 'type_usagers']]

                values = json.loads(df.to_json(orient='records'))
                cache.set('test_data', values, 15 * 60)
                data = values
        return data

    def get_sample_dataset(self) -> list[ParkingModel]:
        """Fetches a sample dataset of parking areas from an external 
        API and returns it as a list of ParkingModel instances."""
        data = self._get_dataset()
        return [ParkingModel(**value) for value in data]

    @serialize(ParkingSerializer)
    def get_sample_serialized_dataset(self) -> list[dict]:
        """Fetches a sample dataset of parking areas from an external
        API and returns it as a list of serialized ParkingModel instances.
        
        Returns:
            list: A list of serialized ParkingModel instances.
        """
        return self._get_dataset()
            
    def addition_tool(self, a: int, b: int) -> int:
        """Add two numbers and return the result.

        Args:
            a (int): The first number to add.
            b (int): The second number to add.
        
        Returns:
            int: The result of the addition.
        """
        return a + b


class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel


class SimpleSerializer(Serializer):
    name = serializers.CharField(max_length=100)


@mcp_publish_list
class ProctedSimpleView(ListAPIView):
    """A protected view that lists all SimpleModel instances.
    
    Returns:
        list: A list of serialized SimpleModel instances.
    """

    permission_classes = (TokenHasReadWriteScope,)
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_list
class SimpleListView(ListAPIView):
    """A simple view that lists all SimpleModel instances.
    
    Returns:
        list: A list of serialized SimpleModel instances.
    """
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_create
class SimpleCreateView(CreateAPIView):
    """A simple view that creates a SimpleModel instance.
    
    Returns:
        dict: A serialized SimpleModel instance.
    """
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


DJANGO_MCP_SERVER.completion()
def autocomplete_names(ref: PromptReference, argument: CompletionArgument, context: CompletionContext):
    if isinstance(ref, PromptReference) and argument.name == 'name':
        names = SimpleModel.objects.values_list('name', flat=True)
        return Completion(values=names) 
