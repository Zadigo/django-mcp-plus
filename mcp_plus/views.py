from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# from oauth2_provider.views.generic import ProtectedResourceView
from rest_framework.views import APIView

from mcp_plus.server.base import DJANGO_MCP_SERVER


class StreamableHttpView(APIView):
    """A Django view that handles requests for the MCP server."""

    mcp_server = DJANGO_MCP_SERVER

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.mcp_server._handle_request(request)

    def post(self, request, *args, **kwargs):
        return self.mcp_server._handle_request(request)

    def delete(self, request, *args, **kwargs):
        self.mcp_server.destroy_session(request)
        return HttpResponse(status=200, content="Session destroyed")

