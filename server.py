from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("add-mcp-http")


# Define a simple tool
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    a = _to_number(a)
    b = _to_number(b)
    return a + b


# Subtract tool
@mcp.tool
def sub(a: int, b: int) -> int:
    """Subtract b from a"""
    a = _to_number(a)
    b = _to_number(b)
    return a - b


# Multiply tool
@mcp.tool
def mul(a: int, b: int) -> int:
    """Multiply two numbers"""
    a = _to_number(a)
    b = _to_number(b)
    return a * b


# Divide tool
@mcp.tool
def div(a: float, b: float) -> float | None:
    """Divide a by b. Returns None on division by zero."""
    a = _to_number(a)
    b = _to_number(b)
    if b == 0:
        return None
    return a / b


def _to_number(x):
    if isinstance(x, (int, float)):
        return x
    try:
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            raise ValueError(f"{x!r} is not a number")


# Rounding tool (named `round`)
@mcp.tool
def round(value: float, ndigits: int = 0) -> float:
    """Round a number to `ndigits` decimal places (default 0)."""
    v = _to_number(value)
    try:
        nd = int(ndigits)
    except Exception:
        raise ValueError(f"ndigits must be integer, got {ndigits!r}")
    return __builtins__['round'](v, nd)


if __name__ == "__main__":
    # Run the server
    mcp.run(transport="http", host="0.0.0.0", port=9999)