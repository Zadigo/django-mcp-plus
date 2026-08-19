from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class McpServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mcp_server"

    def ready(self):
        from mcp_server import checks  # noqa: F401
        
        autodiscover_modules('mcp')
                
        from mcp_server.server.discovery import initialize_toolsets
        initialize_toolsets()
