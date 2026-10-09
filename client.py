import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession


async def main():
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    # Connect to the server using stdio_client
    async with stdio_client(server_params) as streams:
        # Create a session from the streams
        read_stream, write_stream = streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()
            print("Session initialized")

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call ask_chatgpt tool
            print("\n--- Calling ask_chatgpt ---")
            result = await session.call_tool("ask_chatgpt", {"prompt": "What is Python?"})
            print(f"Result: {result}")

            # Call summarize tool
            print("\n--- Calling summarize ---")
            text = "Python is a high-level, interpreted programming language known for its simplicity and readability."
            result = await session.call_tool("summarize", {"text": text})
            print(f"Result: {result}")

            # Call explain_python tool
            print("\n--- Calling explain_python ---")
            code = "x = [i**2 for i in range(10)]"
            result = await session.call_tool("explain_python", {"code": code})
            print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())