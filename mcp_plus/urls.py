from django.conf import settings
from django.urls import path
from django.utils.module_loading import import_string
from rest_framework.permissions import IsAuthenticated

from mcp_plus.views import StreamableHttpView, oauth_protected_resource_metadata

# Register MCP Server View and bypass default DRF 
# default permission / authentication classes
base_url = getattr(settings, 'DJANGO_MCP_PLUS_ENDPOINT', 'mcp')

urlpatterns = [
    path(
        '.well-known/oauth-protected-resource', 
        oauth_protected_resource_metadata
    ),
    path(
        base_url, 
        StreamableHttpView.as_view(
            permission_classes=[IsAuthenticated] if getattr(settings, 'DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES', None) else [],
            authentication_classes=[import_string(cls) for cls in getattr(settings, 'DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES', [])]
        ), 
        name="mcp_plus_streamable_http_endpoint"
    ),
]
