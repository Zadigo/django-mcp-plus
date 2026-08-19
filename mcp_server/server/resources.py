from collections import defaultdict
from typing import ClassVar

from django.apps import apps
from django.conf import settings
from django.db.models import Model
from mcp.server.mcpserver.resources.base import Resource
from mcp.types import (
    Completion,
    CompletionArgument,
    CompletionContext,
    PromptReference,
    ResourceTemplateReference,
)

from mcp_server.typings import TypeDjangoMcpServer


class ResourceManager(type):
    registry: ClassVar[defaultdict[str, list[Resource]]] = defaultdict(list)

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if name != 'Resource' and issubclass(cls, Resource):
            cls.registry['resources'].append({name: cls})

    @classmethod
    def load_resources(cls, server: TypeDjangoMcpServer):
        """Method that loads all registered resources and prompts 
        into the provided server instance.
        
        Args:
            server (TypeDjangoMcpServer): The server instance where resources and prompts will be loaded.
        """
        models: list[Model] = [model for model in apps.get_models()]
        str_models: list[str] = [model._meta.model_name for model in models]

        available_settings: list[str] = []

        # Filter out sensitive configurations strictly to prevent security leakage
        SENSITIVE_KEYWORDS = {'SECRET', 'PASSWORD', 'KEY', 'TOKEN', 'AUTH', 'CREDENTIAL', 'DATABASE'}

        for setting in dir(settings):
            if setting.isupper():
                # Basic security heuristic check
                if any(keyword in setting for keyword in SENSITIVE_KEYWORDS):
                    continue
                available_settings.append(setting)

        available_settings.sort(key=lambda x: x.lower())

        @server.resource("models://{app_label}/{model_name}")
        def get_model_resource(app_label: str, model_name: str) -> str:
            """Returns details about a specific Django model."""
            model = apps.get_model(app_label, model_name)
            fields = [f.name for f in model._meta.get_fields()]
            return f"Model: {app_label}.{model_name}\nFields: {', '.join(fields)}"

        @server.resource('resource://settings')
        def some_resource():
            # Use a single backslash for the newline join syntax
            str_settings = [f"* {value}" for value in available_settings]
            formatted_list = "\n".join(str_settings)

            return f"""# Settings for the Django Project

            Here are the settings that are currently configured in the Django project. You can query these
            settings to understand how the project is configured and to debug any issues that may arise.

            ## Instructions

            * Ensure that you do not expose sensitive information such as SECRET_KEY or database credentials in your queries.
            * Refuse to provide any sensitive information if asked for it.

            ## Django related settings

            {formatted_list}
            """


        @server.prompt(name='get-settings-details')
        def get_settings_details() -> str:
            """A prompt that allows the user to query the settings
            that are currently present in the Django project. Useful
            for debugging and testing purposes."""
            return (
                "Can you provide me with the details of the settings that are "
                "currently configured in the Django project?"
            )


        @server.prompt(name='get-setting-detail')
        def get_setting_detail(setting_name: str) -> str:
            """Allows the user to query a specific setting in the Django project
            by providing the setting name. Useful for debugging and testing purposes.

            Args:
                setting_name: The name of the setting to be queried.
            """
            return f"Can you tell me more about this setting: {setting_name}?"


        @server.prompt(name='debug-error')
        def debugging_an_error(code: str) -> str:
            """A prompt that allows the user to debug a specific error in the Django
            project. Provide the error message to get a detailed explanation and
            possible solutions.

            Args:
                code: The error message to be debugged.
            """
            return f"Please analyze this error that I got from my application:\n\n{code}"
        

        @server.prompt(name='list-of-models')
        def list_of_models() -> str:
            """A prompt that allows the user to get a list of all the models in
            the Django project. Useful for debugging and testing purposes."""
            return "Can you provide me with a list of all the models in the Django project?"


        @server.prompt(name='describe-a-model')
        def describe_a_model(model_name: str) -> str:
            """A prompt that allows the user to get details of a specific model in
            the Django project. Useful for debugging and testing purposes."""
            return f"Can you provide me with details of this model: {model_name}?"


        @server.completion()
        async def handle_completion(ref: PromptReference | ResourceTemplateReference, argument: CompletionArgument, context: CompletionContext | None,) -> Completion | None:
            if isinstance(ref, PromptReference) and argument.name == "model_name":
                return Completion(values=str_models)

            if isinstance(ref, PromptReference) and argument.name == "setting_name":
                # Accepts only the first 100 settings to avoid 
                # overwhelming the user with too many options
                return Completion(values=available_settings[:100])
            return None
