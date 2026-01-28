from llmir import AIRoles, Tool, AIChunkText, AIChunkFile, AIChunkToolCall, AIMessageToolResponse, AIChunks
from .base import LLMState, LLMShared
from edgygraph import Node
from typing import Any, Callable, Type, Tuple, cast
from pydantic import Field, create_model, BaseModel
from docstring_parser import parse
from rich import print as rprint
from datetime import datetime
import json
import inspect
import mcp
import fastmcp
import base64
import mimetypes



class AddToolsNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]): #TODO make it make sense

    tools: dict[str, Tuple[Callable[..., Any], Tool]]

    def __init__(self, functions: list[Callable[..., Any]]) -> None:
        super().__init__()

        self.tools = self.format_functions(functions)

    async def run(self, state: T, shared: S) -> None:
        
        async with shared.lock:
            for key, value in self.tools.items():
                
                if key in shared.tool_functions:
                    raise Exception(f"Duplicate function name: {key}")
                
                function, tool = value

                shared.tool_functions[key] = function
                state.tools.append(tool)

    
    def format_functions(self, functions: list[Callable[..., Any]]) -> dict[str, Tuple[Callable[..., Any], Tool]]:

        tools: dict[str, Tuple[Callable[..., Any], Tool]] = {}

        for function in functions:

            if function.__name__ in tools:
                raise Exception(f"Duplicate function name: {function.__name__}")

            doc = parse(function.__doc__ or "")
            param_descriptions = {p.arg_name: p.description for p in doc.params}

            signature = inspect.signature(function)
            fields = {}

            for name, param in signature.parameters.items():

                # Skip *args or **kwargs
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue

                annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
                default = ... if param.default is inspect.Parameter.empty else param.default

                fields[name] = (
                    annotation, 
                    Field(
                        default=default,
                        description=param_descriptions.get(name, "")
                    )
                )

            dynamic_model: Type[BaseModel] = create_model(function.__name__, **cast(dict[str, Any], fields))

            tools[function.__name__] = (
                function,
                Tool(
                    name=function.__name__,
                    description=doc.description or "",
                    input_schema=dynamic_model.model_json_schema(),
                )
            )
        
        return tools
    


class AddMCPToolsNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    client: fastmcp.Client[Any]

    def __init__(self, url: str) -> None:
        super().__init__()

        self.client = fastmcp.Client(url)

    async def run(self, state: T, shared: S) -> None:
        
        async with self.client:

            tools: list[Tool] = self.format_tools(await self.client.list_tools())

            print("MCP Tools:")
            print(tools)

            state.tools.extend(tools)

            async with shared.lock:
                for tool in tools:
                    async def function(_tool: Tool = tool, **kwargs: Any) -> fastmcp.client.client.CallToolResult:
                        async with self.client:
                            return await self.client.call_tool(
                                name=_tool.name,
                                arguments=kwargs
                            )
                    if tool.name in shared.tool_functions:
                        raise Exception(f"Tool with name \"{tool.name}\" already exists")
                    shared.tool_functions[tool.name] = function

    
    def format_tools(self, mcp_tools: list[mcp.types.Tool]) -> list[Tool]:

        tools: list[Tool] = []

        for mcp_tool in mcp_tools:
            tools.append(
                Tool(
                    name=mcp_tool.name,
                    description=mcp_tool.description or "",
                    input_schema=mcp_tool.inputSchema,
                )
            )

        return tools


class GetToolCallResultsNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    async def run(self, state: T, shared: S) -> None:
        
        async with shared.lock:

            for message in state.new_messages:

                for chunk in message.chunks:

                    if isinstance(chunk, AIChunkToolCall):

                        try:

                            rprint(f"Executing function {chunk.name}")

                            result = await self.run_function(shared, chunk)

                            shared.tool_call_results.append(
                                (
                                    chunk, 
                                    result
                                )
                            )

                            rprint(f"Executed function {chunk.name}")
                            rprint(state)

                        except json.JSONDecodeError as e:
                            e.add_note(f"Error execution function {chunk.name} with arguments {chunk.arguments}")
                            raise e
                        


    async def run_function(self, shared: S, chunk: AIChunkToolCall) -> Any:
        

        func = shared.tool_functions[chunk.name]

        if inspect.iscoroutinefunction(func):
            return await func(**chunk.arguments)
        else:
            return func(**chunk.arguments)

                    



class IntegrateToolResultsNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    async def run(self, state: T, shared: S) -> None:

        async with shared.lock:

            for chunk, result in shared.tool_call_results:

                try:
                    state.new_messages.append(self.format_result(chunk, result))

                except json.JSONDecodeError as e:
                    e.add_note(f"Unable to JSON encode result for function {chunk.name} with arguments {chunk.arguments}")
                    raise e
            
            shared.tool_call_results = []


    def format_result(self, chunk: AIChunkToolCall, result: Any) -> AIMessageToolResponse:

        if not isinstance(result, str):
            result = json.dumps(result)

        return AIMessageToolResponse(
            id=chunk.id,
            name=chunk.name,
            chunks=[
                AIChunkText(
                    text=result,
                )
            ]
        )
    

class IntegrateMCPToolResultsNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    async def run(self, state: T, shared: S) -> None:

        remaining: list[Tuple[AIChunkToolCall, Any]] = []


        async with shared.lock:

            rprint(shared)

            for chunk, result in shared.tool_call_results:

                rprint(chunk)

                if not isinstance(result, fastmcp.client.client.CallToolResult):
                        remaining.append((chunk, result))
                        continue

                try:
                    state.new_messages.append(self.format_result(chunk, result))

                except json.JSONDecodeError as e:
                    e.add_note(f"Unable to JSON encode result for function {chunk.name} with arguments {chunk.arguments}")
                    raise e
            
            shared.tool_call_results = remaining


    def format_result(self, chunk: AIChunkToolCall, result: fastmcp.client.client.CallToolResult) -> AIMessageToolResponse:
        

        result_chunks: list[AIChunks] = []

        for content in result.content:

            match content:
                
                case mcp.types.TextContent():
                    result_chunks.append(
                        AIChunkText(
                            text=content.text
                        )
                    )
                case mcp.types.ImageContent() | mcp.types.AudioContent():
                    bytes = base64.b64decode(content.data)
                    mimetype = content.mimeType
                    ext = mimetypes.guess_extension(mimetype)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name = f"{chunk.name}_{timestamp}{ext}"
                    result_chunks.append(
                        AIChunkFile(
                            name=name,
                            mimetype=mimetype,
                            bytes=bytes
                        )
                    )
                case mcp.types.ResourceLink() | mcp.types.EmbeddedResource():
                    raise NotImplementedError("Handling of ResourceLinks and EmbeddedResources as MCP function results are not yet implemented")
                
        if not result_chunks:
            result_chunks = [
                AIChunkText(
                    text="Empty Result"
                )
            ]

        return AIMessageToolResponse(
            role=AIRoles.TOOL,
            id=chunk.id,
            name=chunk.name,
            chunks=result_chunks
        )
