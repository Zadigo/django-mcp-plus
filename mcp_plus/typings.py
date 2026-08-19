from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

import pydantic
from django.db.models import Model, QuerySet

if TYPE_CHECKING:
    from mcp_plus.server.base import DjangoMcpServer
    from mcp_plus.server.toolset.mixins import McpMethodsToolset, ModelQueryToolset


type TypeDjangoMcpServer = 'DjangoMcpServer'

type TypeToolsetMethodReturn = QuerySet | Model | pydantic.BaseModel | Sequence[Any] | Sequence[pydantic.BaseModel] | None

type TypeToolsetMethod[T = TypeToolsetMethodReturn] = Callable[..., T]

type TypeToolset = McpMethodsToolset | ModelQueryToolset

type TypeMcpToolset = McpMethodsToolset

type TypeModelQueryToolset = ModelQueryToolset
