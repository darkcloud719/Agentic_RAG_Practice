from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv
from rich import print as pprint
import os
import logging
import asyncio
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_4O = os.getenv("AZURE_OPENAI_DEPLOYMENT_4O")

model_client = AzureOpenAIChatCompletionClient(
    model = AZURE_OPENAI_DEPLOYMENT_4O,
    azure_endpoint = AZURE_OPENAI_API_ENDPOINT,
    azure_deployment = AZURE_OPENAI_DEPLOYMENT_4O,
    api_version = AZURE_OPENAI_API_VERSION,
    api_key = AZURE_OPENAI_API_KEY
)

weather_mcp_server = StdioServerParams(
    command="python",
    args=["weather_mcp.py"]
)

async def run_agent(task: str):

    tools = await mcp_server_tools(weather_mcp_server)

    agent = AssistantAgent(
        name="my_agent",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True,
        system_message="You are a weather assistant. You can use two tools: get_today() to know today's date, and get_week_weather() to know the weather for the next 7 days. Use these tools to answer questions about the weather."
    )

    # await Console(agent.run_stream(task=task),output_stats=True)

    result = await agent.run(task=task)

    if result.messages:
        answer = result.messages[-1].content
        pprint(f"[bold green]Answer:[/bold green] {answer}")

if __name__ == "__main__":
    task = "What is the weather be the day after tomorrow?"
    asyncio.run(run_agent(task=task))