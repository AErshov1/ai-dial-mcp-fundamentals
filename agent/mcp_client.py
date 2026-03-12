from typing import Optional, Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt
from pydantic import AnyUrl


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        # 1. Call `streamablehttp_client` method with `mcp_server_url` and assign to `self._streams_context`
        # 2. Call `await self._streams_context.__aenter__()` and assign to `read_stream, write_stream, _`
        # 3. Create `ClientSession(read_stream, write_stream)` and assign to `self._session_context`
        # 4. Call `await self._session_context.__aenter__()` and assign it to `self.session`
        # 5. Call `self.session.initialize()`, and print its result (to check capabilities of MCP server later)
        # 6. return self
        self._streams_context = streamablehttp_client(self.mcp_server_url)
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        self._session_context = ClientSession(
            read_stream=read_stream,
            write_stream=write_stream
        )
        self.session = await self._session_context.__aenter__()
        result = await self.session.initialize()
        if not result:
            raise RuntimeError("Failed to initialize MCP client session.")

        print(f"{'='*80}\nMCP CLIENT SESSION\n\n=> {repr(result)}\n{'='*80}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # This is shutdown method.
        # If session is present and session context is present as well then shutdown the session context (__aexit__ method with params)
        # If streams context is present then shutdown the streams context (__aexit__ method with params)
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._streams_context:
            await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError(
                "MCP client not connected. Call connect() first.")

        # 1. Call `await self.session.list_tools()` and assign to `tools`
        # 2. Return list with dicts with tool schemas. It should be provided according to DIAL specification
        #    https://dialx.ai/dial_api#operation/sendChatCompletionRequest (request -> tools)
        list_tool = await self.session.list_tools()
        result: list[dict[str, Any]] = []
        for tool in list_tool.tools:
            tool_dict = {
                "type": "function",
                "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                }
            }
            result.append(tool_dict)

        return result

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError(
                "MCP client not connected. Call connect() first.")

        # TODO:
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        # 3. print(f"    ⚙️: {content}\n")
        # 4. If `isinstance(content, TextContent)` -> return content.text
        #    else -> return content
        tool_result = await self.session.call_tool(
            name=tool_name,
            arguments=tool_args
        )
        content = tool_result.content[0]
        print(f"{'-'*80}\nTOOL CALL: Content\n\n{content}\n{'-'*80}")
        if isinstance(content, TextContent):
            return content.text

        return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        # Wrap into try/except (not all MCP servers have resources), get `list_resources` (it is async) and resources
        # from it. In case of error print error and return an empty array
        try:
            resources_result: ReadResourceResult = await self.session.list_resources()
            return resources_result.contents
        except Exception as e:
            print(f"Error fetching resources: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        # 1. Get resource by uri (uri is that we provided on the Server side "users-management://flow-diagram")
        # 2. Get contents of [0] resource
        # 3. ResourceContents has 2 types TextResourceContents and BlobResourceContents, in case if content is instance
        #    of TextResourceContents return it is `text`, in case of BlobResourceContents return it is `blob`
        # ---
        # Optional: Later on in app.py you can try to fetch resource and print it (in our case it is image/png provided
        # as bytes, but you can return on the server side some dict just to check how resources are looks like).
        resource = await self.session.read_resource(uri=uri)
        content = resource.contents[0]
        if isinstance(content, TextResourceContents):
            return content.text

        return content.blob

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        # Wrap into try/except (not all MCP servers have prompts), get `list_prompts` (it is async) and prompts
        # from it. In case of error print error and return an empty array
        try:
            prompts_result: GetPromptResult = await self.session.list_prompts()
            return prompts_result.prompts
        except Exception as e:
            print(f"Error fetching prompts: {e}")

        return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        # 1. Get prompt by name
        # 2. Create variable `combined_content` with empty string
        # 3. Iterate through prompt result `messages` and:
        #       - if `message` has attribute 'content' and is instance of TextContent then concat `combined_content`
        #          with `message.content.text + "\n"`
        #       - if `message` has attribute 'content' and is instance of `str` then concat `combined_content` with
        #          with `message.content + "\n"`
        # 4. Return `combined_content`
        prompt_result = await self.session.get_prompt(name=name)
        combined_content = ""
        for msg in prompt_result.messages:
            if isinstance(msg.content, TextContent):
                combined_content += msg.content.text + "\n"
            elif isinstance(msg.content, str):
                combined_content += msg.content + "\n"

        return combined_content
