from django.core.management.base import BaseCommand

from mcp_server.management.utils import Tabs
from mcp_server.server.toolset.mixins import McpMethodsToolset, ModelQueryToolset


class Command(BaseCommand):
    help = 'Returns all the toolsets present on the MCP server'

    def handle(self, *args, **options):
        for key, method in McpMethodsToolset.registry.items():
            template = self.style.SUCCESS(Tabs.PLUS.value) + f'{key}: {method.registry}'
            self.stdout.write(template)

        self.stdout.write(self.style.NOTICE('Model query toolsets:\n'))
        for key, tool in ModelQueryToolset.registry.items():
            template = self.style.SUCCESS(Tabs.PLUS.value) + f'{self.style.HTTP_INFO(key)} -> {tool.model._meta.model_name}'
            self.stdout.write(template)
