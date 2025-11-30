import logging
from mcp.server import FastMCP
from mcp.types import TextContent

mcp_server = FastMCP(name="calculator_mcp_server", instructions="計算機")

@mcp_server.tool()
async def add(x:float, y:float) -> list[TextContent]:
    """
    Adds two numbers and return the result as a list of TextContent.
    :param x: First number
    :param y: Second number
    :return: List of TextContent containing the result
    """
    result = x + y
    return [TextContent(text=f"The result of {x} + {y} is {result}.")]

if __name__ == "__main__":
    mcp_server.run(transport="stdio")