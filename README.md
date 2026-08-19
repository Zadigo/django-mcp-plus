# Django MCP Plus

**Django MCP Plus** implements the MCP (Model-Controller-Presenter) design pattern in Django, providing a structured way to build web applications. It enhances the traditional MVC (Model-View-Controller) architecture by introducing the Presenter layer, which acts as an intermediary between the Model and the View, allowing for better separation of concerns and more maintainable code.

## 🚀 Features

* MCP architecture implementation
* Clear separation of concerns between Model, Controller, and Presenter
* Easy integration with existing Django projects
* Works on both WSGI and ASGI servers
* Supports Django's built-in authentication and authorization system
* Supports any types of MCP clients (Claude AI, Google Agent Development Kit, etc.)

> [!Note]
> This project is a fork from [django-mcp](https://github.com/gts360/django-mcp-server) which is no longer maintained.
> This fork aims to continue the development and maintenance of the project under a different umbrella.

---

## 📦 Installation

Run one of the following commands to install Django MCP Plus:

```bash
# With Pip
pip install django-mcp-plus

# With Poetry
poetry add django-mcp-plus

# With Pipenv
pipenv install django-mcp-plus

# With UV
uv install django-mcp-plus
```

Add the app to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'django_mcp_plus',
    ...
]

Add the following to your `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('mcp/', include('django_mcp_plus.urls')),
    ...
]
```

The server will be available at `http://localhost:8000/mcp/` by default.

---

## 📖 Usage

MCP servers use a simple JSON-based protocol for communication between clients and the server. Clients send requests to the server, which processes them and returns responses.

They expose `tools`, `resources` or `prompts` with which clients can interact.

The Django MCP server is based on the excellent [Python SDK for the Model-Context Protocol](https://py.sdk.modelcontextprotocol.io/) and implements all the features of the protocol.

### 📚 Creating MCP Tools

Django MCP Plus allows the creation of two types of tools based on plain methods or Django models. All MCP tools and features should be placed in an `mcp.py` file in your Django app which will be automatically discovered by the framework.

#### 📌 Tools from plain methods

Plain methods can be exposed as MCP tools by subclassing `McpMethodsToolset` and defining your methods. Each method should have type hints for its parameters and return value, which will be used to generate the tool's schema.

These methods can return anything that is serializable to JSON, including dictionaries, lists, strings, numbers, and booleans.

```python
from mcp_plus.server.toolset import McpMethodsToolset, ModelQueryToolset

class SimpleGenericTool(McpMethodsToolset):
    def get_addition(self, a: int, b: int) -> int:
        """Returns the sum of two integers."""
        return a + b
```

`McpMethodsToolset` is a toolset that allows you to define multiple methods in a single class. Each method can have its own parameters and return type, and the toolset will automatically generate the schema for each method.

They can also return nothing and just be used to perform some action on the server side. In this case, the return type should be `None`.

```python
class SimpleActionTool(McpMethodsToolset):
    def perform_action(self, action: str) -> None:
        """Performs an action on the server side."""
        send_mail(
            subject=subject,
            message=body,
            from_email='your_email@example.com',
            recipient_list=[to_email],
            fail_silently=False,
         )
```

### 📌 Tools from Django models

These tools expect a model from which can be queried and sent to the client.

In its simplest form you can create a tool from a model by subclassing `ModelQueryToolset` and specifying the model to be used.

```python
from mcp_plus.server.toolset import ModelQueryToolset

class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel
```

The class proposes a set of attributes that can be used to manipulate the underlying queryset and the data returned to the client. The attributes are:

**exclude_fields**

Exclude fields from the model that should not be returned to the client. This is useful for sensitive information or fields that are not relevant to the client.

**fields**

Specify the fields from the model that should be returned to the client. If empty, all fields will be returned.

**search_fields**

Specify the fields from the model that should be searchable.

**extra_filters**

Specify additional filters that can be applied to the queryset. The filters follow the MangoDB pipeline syntax and can be used to filter the data returned to the client.

**extra_instructions**

Provide extra instructions for the tool.

**output_format**

Specify the format of the output. Default is `'json'`.

**output_as_resource**

Indicate whether the output should be treated as a resource. Default is `False`.

You can also override the `get_queryset` method to customize the queryset used by the tool.

```python
class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel

    def get_queryset(self):
        """Return a custom queryset."""
        return self.model.objects.filter(is_active=True)
```

### 📌 Tools from Rest Framework views

You can also create tools from Django Rest Framework views by using one of the following decorators:

* mcp_publish_create
* mcp_publish_delete
* mcp_publish_list

By decorating your DRF view class with one of these decorators, you can expose the view as an MCP tool. The decorator will automatically generate the schema for the view and handle the request and response.

```python
@mcp_publish_list
class SimpleListView(ListAPIView):
    """A simple view that lists all SimpleModel instances.
  
    Returns:
        list: A list of serialized SimpleModel instances.
    """
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_create
class SimpleCreateView(CreateAPIView):
    """A simple view that creates a SimpleModel instance.
  
    Returns:
        dict: A serialized SimpleModel instance.
    """
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer


@mcp_publish_delete
class SimpleDeleteView(DestroyAPIView):
    """A simple view that deletes a SimpleModel instance."""
    queryset = SimpleModel.objects.all()
    serializer_class = SimpleSerializer
```

> [!Important]
> Each view should have a docstring that describes the view and its return value. The docstring will be used to generate the tool's schema.

> [!Important]
> The decorators should decorate the view that is related to the tool. For example,
> `mcp_publish_create` will raise an error if it decorates a view that does not create an object.
> Similarly, `mcp_publish_delete` and `mcp_publish_list` should only decorate views that delete and list objects, respectively.

### Tools with Python MCP SDK

You can also create tools using the Python MCP SDK by importing the main server:

**Tools***

```python
from mcp_plus.server.base import erDJANGO_MCP_SERVER

DJANGO_MCP_SERVER.tool()
async def get_addition(a: int, b: int) -> int:
    """Returns the sum of two integers."""
    return a + b
```

**Resources***

```python
from mcp_plus.server.base import DJANGO_MCP_SERVER

DJANGO_MCP_SERVER.resource()
def get_simple_model_resource() -> list[SimpleModel]:
    """Returns a list of SimpleModel instances."""
    return """A list of SimpleModel instances."""
```

**Completion***

```python
from mcp_plus.server.base import DJANGO_MCP_SERVER

DJANGO_MCP_SERVER.completion()
def autocomplete_enames(ref: PromptReference, argument: CompletionArgument, context: CompletionContext):
    if isinstance(ref, PromptReference) and argument.name == 'name':
        names = SimpleModel.objects.values_list('name', flat=True)
        return Completion(values=names)
```

As long as these functions are defined in an `mcp.py` file of your Django app, they will be automatically discovered by the framework and exposed as MCP tools.

## ➕ Returning data from tools

Although the tools can return any data that can be serialized to JSON, there is a special situation where you might want to use a DRF serializer to return data from a tool.

That's where the `serialize` decorator comes in. It allows you to use a DRF serializer to serialize the data returned from a tool.

```python
from rest_framework import serializers

class SimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleModel
        fields = '__all__'


class SimpleModelToolFromTestApp(ModelQueryToolset):
    model = SimpleModel

    @serialize(SimpleModelSerializer)
    def get_dataset(self):
        """Return a dataset of SimpleModel instances."""
        return self.model.objects.all()
```

The data that will be returned to the client will be serialized using the `SimpleModelSerializer` serializer.

## 📖 Usage with MCP Clients

To test your MCP server with a client, you can follow these steps. We will be using `uv` for this demonstration.

### 📌 Testing your server implementation

Before plugin it to a client, you can test your server implementation by running the following commands:

```shell
npx @modelcontextprotocol/inspector uv --directory /path/to/.venv/bin run /path/to/manage.py stdio_server
```

### 📌 Testing your server with a client

You can test your server with a client by running the following commands.

We will be using Claude AI for this demonstration, but you can use any client that supports the MCP protocol.

1. Install Claude Desktop from [claude.ai](https://claude.ai)
2. In the Claude Desktop app, go to `File > Settings > Developer` and click **Edit Config**
3. Add the following configuration to the `config.json` file:

```json
{
    "mcpServers": {
        "test_django_mcp": {
            "command": "/path/to/.venv/bin/python",
            "args": [
                "/path/to/manage.py",
                "stdio_server"
            ]
        }
    }
}
```

That's it! You can now start the server and connect to it from the Claude Desktop app.

> [!Note]
> The path should be the absolute path of your Python virtual environment and the `manage.py` file of your Django project.

## ❌ Authentication and Authorization

> [!Important]
> DRF's authentication and authorization are completely disabled in the Django MCP server.
> Authentication and authorization should be handled using Oauth2 or any other method in the client.

Django MCP Plus supports [DRF&#39;s authentication and authorization system](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) although they are disabled by default.

You can enable them with `DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES`.

## ⚙️ Configuration

Here are the main configuration options for the Django MCP server for your `settings.py` file:

```python
DJANGO_MCP_GLOBAL_SERVER_CONFIG = {
    'name': 'django_mcp_server',  # The name of the server. This will be used to identify the server in the client.
    'instructions': 'This is a Django MCP server.',  # Instructions for the server. This will be shown to the client.
    'stateless': True,  # Whether the server is stateless or not. If True, the server will not store any state between requests.
}

DJANGO_MCP_PLUS_ENDPOINT = 'mcp' # The endpoint for the server. This will be used to access the server from the client.

DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES = [] # The authentication classes for the server. This will be used to authenticate the client. If empty, no authentication will be required.

DJANGO_MCP_PLUS_GET_SERVER_INSTRUCTIONS_TOOL = "" # The tool that will be used to get the server instructions. This will be used to get the instructions for the server from the client. If empty, the instructions will be taken from the `DJANGO_MCP_GLOBAL_SERVER_CONFIG` setting.

DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES = [] # The output renderer classes for the server. This will be used to render the output of the tools. If empty, the default renderer will be used.
```

**DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES**

By default DRF's `JSONRenderer` is used to render the output of the tools. You can specify your own renderer classes to customize the output format.

> [!Note]
> State is managed by [Django session](https://docs.djangoproject.com/en/6.0/topics/http/sessions/) which are saved on the `request.session` object.
> Ensure that your Django project is configured to use the session backend correctly.

> [!Note]
> The session middleware is not required for the Django MCP server to work.

## 🧪 Testing

You can use the commands to run the tests for the Django MCP server:

```bash
# List all the toolsets that are available in the server.
python manage.py list_toolsets

# Shows alls the tools, resources and prompts that are available in the server.
python manage.py mcp_inspect
```

## 📝 Issues

If you encounter bugs or have feature requests, please open an issue on [GitHub Issues](https://github.com/omarbenhamid/django-mcp-server/issues).

## 📝 Contributing

We welcome contributions to Django MCP Plus! If you would like to contribute, please follow these steps:

1. Fork the repository on GitHub.
2. Clone your fork to your local machine.
3. Create a new branch for your changes.
4. Make your changes and commit them.
5. Push your changes to your fork.
6. Open a pull request on GitHub.
