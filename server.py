from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("add-mcp-http")


# Define a simple tool
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


if __name__ == "__main__":
    # Run the server
    mcp.run(transport="http", host="0.0.0.0", port=9999)