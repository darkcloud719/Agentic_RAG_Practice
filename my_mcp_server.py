from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(text: str) -> str:
    return f"Hello, {text}!"


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)