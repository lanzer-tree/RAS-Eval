from typing import Union, Sequence, Callable, Literal
from langchain_core.messages import ToolCall, SystemMessage, AIMessage, HumanMessage, ToolMessage
from .llm import LLM
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.errors import GraphRecursionError
import json
import asyncio
from colorama import Fore
from mcp.server.fastmcp import FastMCP


class ReactAgent(LLM):
    """Basic agent implementation."""
    def __init__(self,
                 model: str,
                 tools: Union[Sequence[BaseTool], ToolNode],
                 temperature: float = 0,
                 stream: bool = True,
                 ) -> None:
        super().__init__(model, temperature, stream)
        self.stream = stream
        prompt = "You are a helpful assistant."
        if self.tool_support:
            self.agent_executor = create_react_agent(self.llm, tools, prompt=prompt)
            self.chain = self.agent_executor
        else:
            pass
        
    def add_system_prompt(self, prompt: str) -> None:
        """
        Add a system prompt to the agent.
        Args:
            prompt: system prompt to add.
        """
        self.system_prompt.append(SystemMessage(content=prompt))

    async def get_stream_completion(self, prompt: str) -> list:
        """
        Get tool call list from the agent.
        Args:
            prompt: User prompt.
        """
        proceed = []
        messages = self.system_prompt + [HumanMessage(content=prompt)]
        try:
            async for chunk in self.chain.astream({"messages": messages}, {"recursion_limit": 25}, stream_mode="values"):
                pass
                # print(f"{Fore.YELLOW}{chunk}{Fore.RESET}", end="", flush=True)
            # print(f"\n{Fore.GREEN}{chunk}{Fore.RESET}")
            for message in chunk["messages"]:
                if isinstance(message, SystemMessage):
                    proceed.append({"type": "SystemMessage", "content": message.content})
                elif isinstance(message, HumanMessage):
                    proceed.append({"type": "HumanMessage", "content": message.content})
                elif isinstance(message, ToolMessage):
                    proceed.append({"type": "ToolMessage", "content": message.content})
                elif isinstance(message, AIMessage):
                    if message.tool_calls:
                        proceed.append({"type": "AIMessage", "tool_calls": message.tool_calls})
                    else:
                        proceed.append({"type": "AIMessage", "content": message.content})
            return proceed
                
        except Exception as error:
            print(error)
            return ["error"]

    def get_completion(self, prompt: str) -> list:
        """
        Get tool call list from the agent.
        Args:
            prompt: User prompt.
        """
        proceed = []
        messages = self.system_prompt + [HumanMessage(content=prompt)]
        try:
            response = self.chain.invoke({"messages": messages}, {"recursion_limit": 25})
        except GraphRecursionError as error:
            response = []
            return ["error"]
        for message in response["messages"]:
            if isinstance(message, SystemMessage):
                proceed.append({"type": "SystemMessage", "content": message.content})
            elif isinstance(message, HumanMessage):
                proceed.append({"type": "HumanMessage", "content": message.content})
            elif isinstance(message, ToolMessage):
                proceed.append({"type": "ToolMessage", "content": message.content})
            elif isinstance(message, AIMessage):
                if message.tool_calls:
                    proceed.append({"type": "AIMessage", "tool_calls": message.tool_calls})
                else:
                    proceed.append({"type": "AIMessage", "content": message.content})
        return proceed
    
    def run_tool(self, prompt: str, tool: StructuredTool):
        proceed = []
        tool_description = {}
        tool_description["name"] = tool.get_input_jsonschema()["title"]
        tool_description["parameters"] = {"type": "object", "properties": tool.get_input_jsonschema()["properties"]}
        print(json.dumps(tool_description, indent=4))
        chain = self.llm.bind_tools([tool_description])
        # messages = 
        messages = self.system_prompt + [HumanMessage(content=prompt)]
        response = chain.invoke(prompt)
        print(response)
        if response.tool_calls:
            proceed.append({"type": "AIMessage", "tool_calls": response.tool_calls})
            tool_result = tool.invoke(response.tool_calls[0]["args"])
            proceed.append({"type": "ToolMessage", "content": tool_result})
        else:
            proceed.append({"type": "AIMessage", "content": response.content})
        return proceed
    
    
    def run(self, prompt: str) -> list:
        """
        Run ReactAgent.

        Args:
            prompts: Input prompts.
        """
        if self.tool_support:
            if self.stream:
                response = asyncio.run(self.get_stream_completion(prompt))
            else:
                response = self.get_completion(prompt)
        else:
            response = []
            for tool in list(self.get_toolkits(format="function").values()):
                tool_response = self.run_tool(prompt, tool)
                # print(json.dumps(tool_response, indent=4))
                response += tool_response
        return response
    
    @classmethod
    def get_toolkits() -> dict[str, StructuredTool] | dict[str, Callable]:
        """Get toolkits from the agent."""
        return []

