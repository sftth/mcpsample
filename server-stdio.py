from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP()


# Define a simple tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


if __name__ == "__main__":
    # Run the server with stdio transport
    mcp.run()
