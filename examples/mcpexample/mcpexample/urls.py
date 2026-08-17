from bird_counter.mcp import second_mcp
from django.contrib import admin
from django.urls import include, path

from mcp_server.views import MCPServerStreamableHttpView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('mcp_server.urls')),
    path("mcpunsecured", MCPServerStreamableHttpView.as_view()),
    path("altmcp", MCPServerStreamableHttpView.as_view(mcp_server=second_mcp))
]
