from django.core.management.base import BaseCommand

from mcp_server.server.base import DJANGO_MCP_SERVER


class Command(BaseCommand):
    help = 'Run the global mcp server over STDIO transport'

    def handle(self, *args, **options):
        DJANGO_MCP_SERVER.run(transport='stdio')
