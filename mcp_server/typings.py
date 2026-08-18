from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pydantic
from django.db.models import QuerySet

if TYPE_CHECKING:
    from mcp_server.server.base import DjangoMcpServer
    from mcp_server.server.toolset.mixins import McpMethodsToolset, ModelQueryToolset


type TypeDjangoMcpServer = 'DjangoMcpServer'

type TypeToolsetMethod = Callable[..., QuerySet | pydantic.BaseModel | Sequence[pydantic.BaseModel] | None]

type TypeToolset = McpMethodsToolset | ModelQueryToolset

type TypeMcpToolset = McpMethodsToolset

type TypeModelQueryToolset = ModelQueryToolset
