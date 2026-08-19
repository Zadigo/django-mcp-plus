```Shell
# 1. Start the Django testApp
python manage.py runserver

# 2. Start the base MCP server (which starts the inspector)
uv run mcp dev /path/to/tests/e2e/test_mcp_server.py

# 2. Start the Django testApp MCP server
run python /path/to/django-mcp-plus/manage.py stdio_server

# 3. Run the client to test the Django MCP server endpoints
python /path/to/django-mcp-plus/tests/e2e/test_mcp_client.py

# MCP inspector

npx @modelcontextprotocol/inspector uv --directory /Volumes/Coding/Projects/Open-Source/django-mcp-plus/.venv/bin run /Volumes/Coding/Projects/Open-Source/django-mcp-plus/manage.py stdio_server

npx @modelcontextprotocol/inspector uv --directory /Volumes/Coding/Projects/Open-Source/django-mcp-plus/.venv/bin run /Volumes/Coding/Projects/Open-Source/django-mcp-plus/examples/mcpexample/manage.py stdio_server
```
