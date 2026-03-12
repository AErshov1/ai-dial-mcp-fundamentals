import asyncio
import json
import os

from mcp import Resource
from mcp.types import Prompt

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

API_KEY = os.getenv('DIAL_API_KEY')
DIAL_ENDPOINT = 'https://ai-proxy.lab.epam.com'


# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

async def main():
    # TODO:
    # 1. Create MCP client and open connection to the MCP server (use `async with {YOUR_MCP_CLIENT} as mcp_client`),
    #    mcp_server_url="http://localhost:8005/mcp"
    # 2. Get Available MCP Resources and print them
    # 3. Get Available MCP Tools, assign to `tools` variable, print tool as well
    # 4. Create DialClient
    # 5. Create list with messages and add there SYSTEM_PROMPT with instructions to LLM
    # 6. Add to messages Prompts from MCP server as User messages
    # 7. Create console chat (infinite loop + ability to exit from chat + preserve message history after the call to dial client)
    async with MCPClient('http://localhost:8005/mcp') as mcp_client:
        resources = await mcp_client.session.list_resources()
        print(f"{'='*80}\nMCP RESOURCES\n\n=> {repr(resources)}\n{'='*80}")

        tools = await mcp_client.get_tools()
        print(f"{'='*80}\nMCP TOOLS\n\n=> Tools number: {len(tools)}\n{'='*80}")

        dial_client = DialClient(
            api_key=API_KEY,
            endpoint=DIAL_ENDPOINT,
            mcp_client=mcp_client,
            tools=tools
        )

        chat_history = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]
        prompts_result: list[Prompt] = await mcp_client.get_prompts()
        for prompt in prompts_result:
            if prompt:
                print(f"{'-'*80}\nMCP PROMPT\n\n=> {repr(prompt)}\n{'-'*80}")
                prompt_content = await mcp_client.get_prompt(name=prompt.name)
                if prompt_content:
                    chat_history.append(
                        Message(role=Role.USER, content=prompt_content)
                    )

        print(repr(chat_history))

        while True:
            user_input = input("=> ")
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting chat. Goodbye!")
                break

            chat_history.append(Message(role=Role.USER, content=user_input))
            ai_message = await dial_client.get_completion(chat_history)
            chat_history.append(ai_message)
            print(f"AI: {ai_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
