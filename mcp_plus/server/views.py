from types import SimpleNamespace
from typing import Any

from django.http import HttpRequest
from mcp.server.context import Context
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from mcp_plus.exceptions import ViewClassSubclassError

# from mcp_server.server.session_authentication import resolve_request_from_headers
from mcp_plus.server.toolset.methods import DJANGO_REQUEST_CONTEXT
from mcp_plus.typings import TypeDjangoMcpServer


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

    def __new__(cls, server: TypeDjangoMcpServer, mcp_request: HttpRequest, method: str, body_json: dict | None = None, id: int | None = None):
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

        if getattr(mcp_request, 'user', None):
            request.user = mcp_request.user
            
        if getattr(mcp_request, 'session', None):
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


class ViewMixin[T = APIView]:
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[T], actions: dict | None = None):
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

    def __call__(self, **kwargs: Any):
        """Calls the view with a wrapped request object 
        and returns the response data."""
        # request = RequestWrapper(self.server, DJANGO_REQUEST_CONTEXT.get(SimpleNamespace()), 'GET')
        # return self.view(request).data

        context: Context | None = kwargs.get('_context')
        wrapper_kwargs = kwargs.get('wrapper_kwargs', {})
        view_kwargs = kwargs.get('view_kwargs', {})

        return self.call_view_with_params('GET', context=context, wrapper_kwargs=wrapper_kwargs, view_kwargs=view_kwargs)

    def call_view_with_params(self, method: str, context: Context | None = None, view_kwargs: dict | None = None, wrapper_kwargs: dict | None = None) -> list[dict] | dict | None:
        """Calls the Django HttpRequest view with a wrapped request object and returns the response data.
        
        Args:
            method (str): The HTTP method to use for the request (e.g., 'GET', 'POST', 'PUT', 'DELETE').
            context (Context | None): The context object to use for the request. Defaults to None.
            view_kwargs (dict | None): The keyword arguments to pass to the view. Defaults to None.
            wrapper_kwargs (dict | None): The keyword arguments to pass to the RequestWrapper. Defaults to None.

        Returns:
            The response data from the view.
        """
        # headers = getattr(context, 'headers', None) if context is not None else None
        # wrapped_request = RequestWrapper(self.server, resolve_request_from_headers(headers), 'GET')
        # return self.view(wrapped_request).data
    
        mcp_request = DJANGO_REQUEST_CONTEXT.get(SimpleNamespace())
        wrapped_request = RequestWrapper(self.server, mcp_request, method, **(wrapper_kwargs or {}))
        return self.view(wrapped_request, **(view_kwargs or {})).data


class DrfListViewTool(ViewMixin, BaseApiViewTool[ListAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[ListAPIView], actions: dict | None = None):
        if not issubclass(view_class, ListAPIView):
            raise ViewClassSubclassError(view_class, ListAPIView)
        super().__init__(server, view_class, actions=actions) 


class DrfCreateViewTool(ViewMixin, BaseApiViewTool[CreateAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[CreateAPIView], actions: dict | None = None):
        if not issubclass(view_class, CreateAPIView):
            raise ViewClassSubclassError(view_class, CreateAPIView)
        super().__init__(server, view_class, actions=actions)

    def __call__(self, body: dict, **kwargs: Any):
        # mcp_request = DJANGO_REQUEST_CONTEXT.get(SimpleNamespace())
        # request = RequestWrapper(self.server, mcp_request, 'POST', body_json=body)
        # return self.view(request).data

        context: Context = kwargs.get('_context', None)
        return self.call_view_with_params('POST', context=context, wrapper_kwargs={'body_json': body})
    

class DrfRetrieveViewTool(ViewMixin, BaseApiViewTool[RetrieveAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[RetrieveAPIView], actions: dict | None = None):
        if not issubclass(view_class, RetrieveAPIView):
            raise ViewClassSubclassError(view_class, RetrieveAPIView)
        super().__init__(server, view_class, actions=actions)

    def __call__(self, id: int):
        view_params = {(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}
        return self.call_view_with_params('GET', view_kwargs=view_params)


class DrfUpdateViewTool(ViewMixin, BaseApiViewTool[UpdateAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[UpdateAPIView], actions: dict | None = None):
        if not issubclass(view_class, UpdateAPIView):
            raise ViewClassSubclassError(view_class, UpdateAPIView)
        super().__init__(server, view_class, actions=actions)

    def __call__(self, id: int, body: dict):
        view_params = {(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}
        return self.call_view_with_params('PUT', view_kwargs=view_params, wrapper_kwargs={'id': id, 'body_json': body})
        
        # mcp_request = DJANGO_REQUEST_CONTEXT.get(SimpleNamespace())
        # request = RequestWrapper(self.server, mcp_request, 'PUT', id=id, body_json=body)
        # return self.view(request, **{(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}).data


class DrfDeleteViewTool(ViewMixin, BaseApiViewTool[DestroyAPIView]):
    def __init__(self, server: TypeDjangoMcpServer, view_class: type[DestroyAPIView], actions: dict | None = None):
        if not issubclass(view_class, DestroyAPIView):
            raise ViewClassSubclassError(view_class, DestroyAPIView)
        super().__init__(server, view_class, actions=actions)

    def __call__(self, id: int):
        view_params = {(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}
        return self.call_view_with_params('DELETE', view_kwargs=view_params)
    
        # mcp_request = DJANGO_REQUEST_CONTEXT.get(SimpleNamespace())
        # request = RequestWrapper(self.server, mcp_request, 'DELETE')
        # return self.view(request, **{(self.view.view_class.lookup_url_kwarg or self.view.view_class.lookup_field): id}).data
