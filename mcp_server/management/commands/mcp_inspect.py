import enum

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from mcp import Client

from mcp_server.server.base import DJANGO_MCP_SERVER


class Tabs(enum.Enum):
    TAB = '   '
    TAB_PLUS = '   + '


class Command(BaseCommand):
    help = 'Inspect installed tools, resources and prompts'

    def handle(self, *args, **options):
        async_to_sync(self.inspect)()

    async def inspect(self):
        # This executes purely in-memory with zero subprocess or network overhead.
        async with Client(DJANGO_MCP_SERVER) as client:
            # 1. Discover Tools
            self.stdout.write(self.style.HTTP_INFO("Tools discovered in server:"))
            result = await client.list_tools()
            for tool in result.tools:
                # : {tool.description}
                self.stdout.write(self.style.SUCCESS(Tabs.TAB_PLUS.value) + f"{tool.name}")
                # self.stdout.write(f"      - {tool.input_schema}")

            # # 2. Discover Resources
            # self.stdout.write("\nResources discovered in server:")
            # resource_list = await client.list_resources()
            # for resource in resource_list.resources:
            #     self.stdout.write(f'\t{resource.name}: {resource.description}')

            # # 3. Discover Prompts
            # self.stdout.write("\nPrompts discovered in server:")
            # prompt_list = await client.list_prompts()
            # for prompt in prompt_list.prompts:
            #     self.stdout.write(f'\t{prompt.name}: {prompt.description}')
