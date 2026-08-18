```Shell
# 1. Start the Django testApp
python manage.py runserver
# 2. (Optional) start the base MCP server
uv run mcp dev tests/e2e/test_mcp_server.py
# 2. Start the Django testApp MCP server
run python ~/django-mcp-plus/manage.py stdio_server
# 3. Run the client to test the Django MCP server endpoints
python ~/django-mcp-plus/tests/e2e/test_mcp_client.py
```
