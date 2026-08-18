from types import SimpleNamespace
from typing import Any

from django.http import HttpRequest
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from mcp_server.server.toolset.methods import DJANGO_REQUEST_CONTEXT
from mcp_server.typings import TypeDjangoMcpServer


class RequestWrapper(HttpRequest):
    """A wrapper around the Django HttpRequest object that 
    allows for the creation of a request object with a specific method, path, and body. 
    This class is used to create a request object that can be passed to the API views 
    in the MCP server.
    
    Args:
        server (TypeDjangoMcpServer): The Django MCP server instance.
        mcp_request (HttpRequest): The original Django request object.
        method (str): The HTTP method to use for the request (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        body_json (dict, optional): The JSON body to include in the request. Defaults to None.
        id (int, optional): The ID to include in the request path. Defaults to None.
    """

    def __new__(cls, server: TypeDjangoMcpServer, mcp_request: HttpRequest, method: str, body_json: dict| None=None, id: int | None=None):
        factory = APIRequestFactory()

        path = f'/_djangomcpserver/{server.name}'

        if id is not None:
            path = f'{path}/{id}'

        match method.upper():
            case 'GET':
                request = factory.get(path)
            case 'POST':
                request = factory.post(path, data=body_json, format='json')
            case 'PUT':
                request = factory.put(path, data=body_json, format='json')
            case 'DELETE':
                request = factory.delete(path)
            case _:
                raise ValueError(f"Unsupported HTTP method: {method}")

        if mcp_request.user:
            request.user = mcp_request.user

        if mcp_request.session:
            request.session = mcp_request.session

        return request


class BaseApiViewTool[T = APIView]:
    """A base class for API views that can be 
    registered as toolset methods in the MCP server.
    
    Args:
        view_class (type): The API view class to register.
    """

    view: type[T] = None

    def __init__(self, view_class: type[T], **kwargs: Any):
        self.view = view_class.as_view(**kwargs)


class ViewMixin:
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[APIView], actions: dict | None = None):
        self.server = server
        self.view = view_class

        def raise_exception(e: Exception):
            raise e

        kwargs = {
            'filter_backends': [],
            'authentication_classes': [],
            'permission_classes': view_class.permission_classes,
            'handle_exception': raise_exception
        }

        if issubclass(view_class, ListAPIView):
            kwargs['pagination_class'] = view_class.pagination_class

        if actions is not None:
            kwargs['actions'] = actions

        # Disables the authentication_classes from the view_class to avoid conflicts
        # in order for django-mcp-plus to handle authentication and authorization.
        super().__init__(view_class, **kwargs)

    def __call__(self):
        """Calls the view with a wrapped request object 
        and returns the response data."""
        request = RequestWrapper(
            self.server,
            DJANGO_REQUEST_CONTEXT.get(SimpleNamespace()),
            'GET'
        )

        return self.view(request).data


class DrfListViewTool(ViewMixin, BaseApiViewTool[ListAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[ListAPIView], actions: dict | None = None):
        if not issubclass(view_class, ListAPIView):
            raise TypeError("view_class must be a subclass of ListAPIView")
        super().__init__(server, view_class, actions=actions) 


class DrfCreateViewTool(ViewMixin, BaseApiViewTool[CreateAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[CreateAPIView], actions: dict | None = None):
        if not issubclass(view_class, CreateAPIView):
            raise TypeError("view_class must be a subclass of CreateAPIView")
        super().__init__(server, view_class, actions=actions)

    def __call__(self, body: dict):
        request = RequestWrapper(
            self.server,
            DJANGO_REQUEST_CONTEXT.get(SimpleNamespace()),
            'POST',
            body_json=body
        )

        return self.view(request).data
    

class DrfRetrieveViewTool(ViewMixin, BaseApiViewTool[RetrieveAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[RetrieveAPIView], actions: dict | None = None):
        if not issubclass(view_class, RetrieveAPIView):
            raise TypeError("view_class must be a subclass of RetrieveAPIView")
        super().__init__(server, view_class, actions=actions)


class DrfUpdateViewTool(ViewMixin, BaseApiViewTool[UpdateAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[UpdateAPIView], actions: dict | None = None):
        if not issubclass(view_class, UpdateAPIView):
            raise TypeError("view_class must be a subclass of UpdateAPIView")
        super().__init__(server, view_class, actions=actions)

    def __call__(self, id: int, body: dict):
        request = RequestWrapper(
            self.server,
            DJANGO_REQUEST_CONTEXT.get(SimpleNamespace()),
            'PUT',
            id=id,
            body_json=body
        )

        return self.view(request, **{(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}).data


class DrfDeleteViewTool(ViewMixin, BaseApiViewTool[DestroyAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[DestroyAPIView], actions: dict | None = None):
        if not issubclass(view_class, DestroyAPIView):
            raise TypeError("view_class must be a subclass of DestroyAPIView")
        super().__init__(server, view_class, actions=actions)

    def __call__(self, id: int):
        request = RequestWrapper(
            self.server,
            DJANGO_REQUEST_CONTEXT.get(SimpleNamespace()),
            'DELETE'
        )

        return self.view(request, **{(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}).data
