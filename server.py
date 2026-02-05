from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("add-mcp-http")


# Define a simple tool
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


# Subtract tool
@mcp.tool
def sub(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b


# Multiply tool
@mcp.tool
def mul(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


# Divide tool
@mcp.tool
def div(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError on division by zero."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


# Rounding tool
@mcp.tool
def round_value(value: float, ndigits: int = 0) -> float:
    """Round a number to `ndigits` decimal places (default 0)."""
    return round(value, ndigits)


if __name__ == "__main__":
    # Run the server
    mcp.run(transport="http", host="0.0.0.0", port=9999)