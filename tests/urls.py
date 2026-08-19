from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.module_loading import import_string
from oauth2_provider import urls as oauth2_urls
from rest_framework.permissions import AllowAny, IsAuthenticated

from mcp_plus.views import StreamableHttpView

base_url = getattr(settings, 'DJANGO_MCP_PLUS_ENDPOINT', 'mcp')

permission_classes = [IsAuthenticated] if getattr(settings, 'DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES', None) else [AllowAny]

authentication_classes = [import_string(cls) for cls in getattr(settings, 'DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES', [])]

urlpatterns = [
    path('admin/', admin.site.urls),
    path("o/", include(oauth2_urls)),
    path(
        base_url,
        StreamableHttpView.as_view(
            permission_classes=permission_classes,
            authentication_classes=authentication_classes
        ),
        name="django_mcp_plus_http_endpoint"
    )
]
