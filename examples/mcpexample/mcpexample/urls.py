from bird_counter.mcp import second_mcp
from django.contrib import admin
from django.urls import include, path

from mcp_plus.views import StreamableHttpView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('mcp_server.urls')),
    path("mcpunsecured", StreamableHttpView.as_view()),
    path("altmcp", StreamableHttpView.as_view(mcp_server=second_mcp))
]
