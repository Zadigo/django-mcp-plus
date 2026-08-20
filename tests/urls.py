from django.contrib import admin
from django.urls import include, path
from oauth2_provider import urls as oauth2_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path("o/", include(oauth2_urls)),
    path('', include('mcp_plus.urls'))
]
