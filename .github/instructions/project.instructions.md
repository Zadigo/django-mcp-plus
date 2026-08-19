---
name: Project Instructions
applyTo: "**/*"
description: "Use when editing any part of the project, including frontends, backends, services, and shared libraries."
---
# Project instructions

## Tech Stack

* Python 3

## Repository structure

```text
mcp_plus
├── management
│   └── commands
├── migrations
└── server
    └── toolset
```

* **server/** Contains the main backend code for the MCP server, including management commands, migrations, and the toolset for server operations.

## Commands

- Test App: in the project root `python manage.py runserver`
- Run base MCP server: `cd tests/e2e && uv run mcp dev test_mcp_server.py`
- Run base MCP client: `cd tests/e2e && uv run mcp dev test_mcp_client.py`
- Tests: `pytest -v --tb=short --disable-warnings --maxfail=1`
- Unit Tests: `pytest -v --tb=short --disable-warnings --maxfail=1 -m unit`
- Run example Django MCP server project: `cd example/mcpexample && uv run python manage.py runserver`
