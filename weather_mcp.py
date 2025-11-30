from mcp.server import FastMCP
from datetime import datetime, timedelta

mcp_server = FastMCP("Weather MCP Server", instructions="提供天氣資訊的服務")

@mcp_server.tool()
def get_today() -> str:
    """Returns today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

@mcp_server.tool()
def get_weather() -> list:
    """
    Return a list of 7 days of weather.
    Each item is a dict: {"date":"YYYY-MM-DD", "weather":"sunny/cloudy/rainy"}
    """
    base_date = datetime.now()
    weather_types = ["sunny","cloudy","rainy","Windy","stormy","snowy","foggy"]
    week_weather = []
    for i in range(7):
        day = base_date + timedelta(days=i)
        weather = weather_types[i % len(weather_types)]
        week_weather.append({"date":day.strftime("%Y-%m-%d"), "weather":weather})
    return week_weather

if __name__ == "__main__":
    mcp_server.run(transport="stdio")