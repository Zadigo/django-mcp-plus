from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, Tags.compatibility)
def check_django_mcp_plus_settings(**kwargs):
    endpoint = getattr(settings, 'DJANGO_MCP_PLUS_ENDPOINT', None)

    if endpoint is not None and not isinstance(endpoint, str):
            return [
                Error(
                    "DJANGO_MCP_PLUS_ENDPOINT must be a string.",
                    id="mcp.E001",
                )
            ]

    authentication_classes = settings.DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES
    if authentication_classes is not None:
        if not isinstance(authentication_classes, list):
            return [
                Error(
                    "DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES must be a list.",
                    id="mcp.E002",
                )
            ]

        for value in authentication_classes:
            if not isinstance(value, str):
                return [
                    Error(
                        "DJANGO_MCP_PLUS_AUTHENTICATION_CLASSES must be a list of strings.",
                        id="mcp.E003",
                    )
                ]

    server_instructions_tool = getattr(settings, 'DJANGO_MCP_PLUS_GET_SERVER_INSTRUCTIONS_TOOL', None)
    if server_instructions_tool is not None and not isinstance(server_instructions_tool, str):
        return [
            Error(
                "DJANGO_MCP_PLUS_GET_SERVER_INSTRUCTIONS_TOOL must be a string.",
                id="mcp.E004",
            )
        ]

    output_renderer_classes = getattr(settings, 'DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES', None)
    if output_renderer_classes is not None:
        if not isinstance(output_renderer_classes, list):
            return [
                Error(
                    "DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES must be a list.",
                    id="mcp.E005",
                )
            ]

        for value in output_renderer_classes:
            if not isinstance(value, str):
                return [
                    Error(
                        "DJANGO_MCP_PLUS_OUTPUT_RENDERER_CLASSES must be a list of strings.",
                        id="mcp.E006",
                    )
                ]
    return []
