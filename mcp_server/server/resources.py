from collections import defaultdict
from typing import ClassVar

from mcp.server.mcpserver.prompts.base import Prompt
from mcp.server.mcpserver.resources.base import Resource

from mcp_server.typings import TypeDjangoMcpServer


class ResourceManager(type):
    registry: ClassVar[defaultdict[str, list[Resource]]] = defaultdict(list)

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'Resource' and issubclass(cls, Resource):
            cls.registry['resources'].append({name: cls})

    @classmethod
    def load_resources(cls, server: TypeDjangoMcpServer):
        """Method that loads all registered resources and prompts 
        into the provided server instance.
        
        Args:
            server (TypeDjangoMcpServer): The server instance where resources and prompts will be loaded.
        """

        server.resource(
            uri='resource://some-resource',
            title='some title',
            description='Some description',
        )

        prompts = [
            Prompt(
                name='review_settings',
                title='A prompt that reviews the settings of the server and provides feedback.',
                description='This prompt is designed to analyze the server settings and provide constructive feedback for optimization.',
                arguments={
                    'settings': 'A dictionary containing the server settings to be reviewed.'
                },
            )
        ]

        for prompt in prompts:
            server.add_prompt(prompt)

