from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pydantic
from django.db.models import QuerySet

if TYPE_CHECKING:
    from mcp_server.server.base import DjangoMcpServer


type TypeDjangoMcpServer = 'DjangoMcpServer'

type TypeToolsetMethod = Callable[..., QuerySet | pydantic.BaseModel | Sequence[pydantic.BaseModel] | None]
