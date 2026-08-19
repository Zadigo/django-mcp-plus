from django.core.management.base import BaseCommand

from mcp_server.server.base import DJANGO_MCP_SERVER


class Command(BaseCommand):
    help = 'Run the global mcp server over STDIO transport'
    requires_system_checks = ()

    def add_arguments(self, parser):
        parser.add_argument(
            '--mcp-host',
            default='127.0.0.1',
            help='Specify the host for the STDIO server'
        )
        parser.add_argument(
            '--mcp-port',
            type=int,
            default=8002,
            help='Specify the port for the STDIO server'
        )

    def handle(self, *args, **options):
        DJANGO_MCP_SERVER.run(transport='stdio')
