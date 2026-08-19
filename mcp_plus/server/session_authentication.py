from collections.abc import Mapping
from types import SimpleNamespace

from django.contrib.auth import get_user_model

MCP_SESSION_ID_HEADER = 'Mcp-Session-Id'

AUTH_USER_SESSION_KEY = '_mcp_auth_user_id'


def _get_header(headers: Mapping | None, name: str) -> str | None:
    """Case-insensitive header lookup that tolerates dicts or Starlette Headers."""
    if not headers:
        return None
    
    for key in (name, name.lower(), name.upper()):
        value = headers.get(key)
        if value is not None:
            return value

    return None


def resolve_request_from_headers(headers: Mapping | None) -> SimpleNamespace:
    """Rebuild a lightweight stand-in for the Django request tied to the
    JSON-RPC call currently executing, resolved from the persisted MCP
    session store rather than from DJANGO_REQUEST_CONTEXT.

    In stateful mode, tool execution runs inside the long-lived per-session
    dispatch task spawned once at session creation. That task's contextvars
    are frozen at spawn time and never observe values set by
    DJANGO_REQUEST_CONTEXT.set(...) in later, per-request calls that merely
    feed bytes into the session's transport stream. The MCP session id
    travels with every call as the 'Mcp-Session-Id' header instead, so we
    use it to look up the authenticated user from durable, shared session
    storage that any thread/task can read.
    """
    from mcp_plus.server.base import DJANGO_MCP_SERVER

    fallback = SimpleNamespace(user=None, session=None)

    session_key = _get_header(headers, MCP_SESSION_ID_HEADER)
    if not session_key:
        return fallback

    store = DJANGO_MCP_SERVER.session_store(session_key=session_key)
    if not store.exists():
        return fallback

    user = None
    user_id = store.get(AUTH_USER_SESSION_KEY)
    if user_id is not None:
        UserModel = get_user_model()
        
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            user = None

    return SimpleNamespace(user=user, session=store)
