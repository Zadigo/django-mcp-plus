import json

import httpx2
import pandas
from django.core.cache import cache
from mcp_types import Completion, CompletionArgument, CompletionContext, PromptReference
from pydantic import BaseModel, model_validator
from rest_framework import serializers
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.serializers import Serializer

from mcp_server.decorators import (
    mcp_publish_create,
    mcp_publish_list,
)
from mcp_server.server.base import DJANGO_MCP_SERVER
from mcp_server.server.toolset import McpMethodsToolset, ModelQueryToolset
from tests.testapp.models import SimpleModel


class ParkingModel(BaseModel):
    nb_places: int
    gratuit: bool
    type_usagers: str

    @model_validator(mode='wrap')
    @classmethod
    def validate_gratuit(cls, data, handler):
        if isinstance(data['gratuit'], str):
            return data['gratuit'] == 'true'
        return False


class SimpleGenericTool(McpMethodsToolset):
    async def _get_dataset(self):
        url = 'https://hub.huwise.com/api/explore/v2.1/catalog/datasets/osm-france-parking-area/records/?lang=fr&limit=10&offset=0'
        data = cache.get('test_data', None)
        if data is None:
            async with httpx2.AsyncClient() as client:
                response = await client.get(url)
                results = response.json()['results']

                df = pandas.DataFrame(results)
                df = df[['nb_places', 'gratuit', 'type_usagers']]

                values = json.loads(df.to_json(orient='records'))
                cache.set('test_data', values, 15 * 60)
                return values

    async def get_sample_dataset(self):
        """Fetches a sample dataset of parking areas from an external 
        API and returns it as a list of ParkingModel instances."""
        data = await self._get_dataset()
        return [ParkingModel(**value) for value in data]
            
    def additional_tool(self, a: int, b: int) -> int:
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
class SimpleListView(ListAPIView):
    """A simple view that lists all SimpleModel instances."""
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_create
class SimpleCreateView(CreateAPIView):
    """A simple view that creates a SimpleModel instance."""
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


DJANGO_MCP_SERVER.completion()
def autocomplete_names(ref: PromptReference, argument: CompletionArgument, context: CompletionContext):
    if isinstance(ref, PromptReference) and argument.name == 'name':
        names = SimpleModel.objects.values_list('name', flat=True)
        return Completion(values=names) 
