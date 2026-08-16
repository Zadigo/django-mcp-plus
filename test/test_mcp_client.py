from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    # Connect to a streamable HTTP server
    async with streamable_http_client("http://localhost:8000/mcpunsecured") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # Call a tool
            tool_result = await session.call_tool("get_species_count", {"name": "e"})
            print(tool_result)

            tool_result = await session.call_tool("get_species_count", {"name": "e"})
            print(tool_result)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
