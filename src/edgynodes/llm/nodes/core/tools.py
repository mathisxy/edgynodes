from llmir import AIRoles, AIChunkText, AIChunkFile, AIChunkToolCall, AIMessageToolResponse, AIChunks
import llmir
from edgygraph import Node
from typing import Any, Callable, Tuple, cast, overload
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


from ...states import StateProtocol, SharedProtocol
from .utils.tools import MCPToolFunction, ToolContext
    

class AddToolsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    tools: dict[str, Tuple[Callable[..., Any], llmir.Tool]]

    def __init__(self, functions: list[Callable[..., Any]]) -> None:
        super().__init__()

        self.tools = self.format_functions(functions)

    async def __call__(self, state: T, shared: S) -> None:
        
        async with shared.lock:
            for key, value in self.tools.items():
                
                if key in shared.llm.tool_functions:
                    raise Exception(f"Duplicate function name: {key}")
                
                function, tool = value

                shared.llm.tool_functions[key] = function
                state.llm.tools.append(tool)

    
    def format_functions(self, functions: list[Callable[..., Any]]) -> dict[str, Tuple[Callable[..., Any], llmir.Tool]]:

        tools: dict[str, Tuple[Callable[..., Any], llmir.Tool]] = {}

        for function in functions:

            if function.__name__ in tools:
                raise Exception(f"Duplicate function name: {function.__name__}")

            doc = parse(function.__doc__ or "")
            param_descriptions = {p.arg_name: p.description for p in doc.params}

            signature = inspect.signature(function)
            fields = {}

            for name, param in signature.parameters.items():

                # Skip *args or **kwargs and context parameters
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) or ToolContext.is_context_param(param):
                    continue

                print(param)

                annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
                default = ... if param.default is inspect.Parameter.empty else param.default

                fields[name] = (
                    annotation, 
                    Field(
                        default=default,
                        description=param_descriptions.get(name, "")
                    )
                )

            dynamic_model: type[BaseModel] = create_model(function.__name__, **cast(dict[str, Any], fields))

            tools[function.__name__] = (
                function,
                llmir.Tool(
                    name=function.__name__,
                    description=doc.description or "",
                    input_schema=dynamic_model.model_json_schema(),
                )
            )
        
        return tools

    


class AddMCPToolsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    client: fastmcp.Client[Any]

    @overload
    def __init__(self, client: fastmcp.Client[Any], /) -> None: ...

    @overload
    def __init__(self, url: str, /) -> None: ...


    def __init__(self, target: str | fastmcp.Client[Any]) -> None:

        if isinstance(target, fastmcp.Client):
            self.client = target
        else:
            self.client = fastmcp.Client(target)


    async def __call__(self, state: T, shared: S) -> None:
        
        async with self.client:

            tools: list[llmir.Tool] = self.format_tools(await self.client.list_tools())

            state.llm.tools.extend(tools)

            async with shared.lock:
                for tool in tools:
                    function = MCPToolFunction(
                        tool,
                        self.client,
                    )

                    if tool.name in shared.llm.tool_functions:
                        raise Exception(f"Tool with name \"{tool.name}\" already exists")
                    shared.llm.tool_functions[tool.name] = function

    
    def format_tools(self, mcp_tools: list[mcp.types.Tool]) -> list[llmir.Tool]:

        tools: list[llmir.Tool] = []

        for mcp_tool in mcp_tools:
            tools.append(
                llmir.Tool(
                    name=mcp_tool.name,
                    description=mcp_tool.description or "",
                    input_schema=mcp_tool.inputSchema,
                )
            )

        return tools


class ExtractNewToolCallsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    async def __call__(self, state: T, shared: S) -> None:
        
        async with shared.lock:

            for message in state.llm.new_messages:

                for chunk in message.chunks:

                    if isinstance(chunk, AIChunkToolCall):

                        shared.llm.new_tool_calls.append(chunk)
                        


class GetNextToolCallResultNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):


    async def __call__(self, state: T, shared: S) -> None:
        
        async with shared.lock:

            if not shared.llm.new_tool_calls:
                raise Exception("No new tool calls available to process")
            
            chunk = shared.llm.new_tool_calls.pop(0)
            
        try:

            rprint(f"Executing function {chunk.name}")

            result = await self.run_function(state, shared, chunk)

            async with shared.lock:
                shared.llm.new_tool_call_results.append(
                    (
                        chunk, 
                        result
                    )
                )

            rprint(f"Executed function {chunk.name}")

        except json.JSONDecodeError as e:
            e.add_note(f"Error execution function {chunk.name} with arguments {chunk.arguments}")
            raise e
                    


    async def run_function(self, state: T, shared: S, chunk: AIChunkToolCall) -> Any:
    
        func = shared.llm.tool_functions[chunk.name]
        sig = inspect.signature(func)

        bound = sig.bind_partial(**chunk.arguments)

        print(bound)

        for name, param in sig.parameters.items():

            if name in bound.arguments: # only use unbound parameters
                continue

            if ToolContext.is_context_param(param):
                context = ToolContext(state, shared)
                bound.arguments[name] = context

        result = func(*bound.args, **bound.kwargs)

        if inspect.iscoroutine(result):
            result = await result

        return result

                    



class IntegrateToolResultsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:

            for chunk, result in shared.llm.new_tool_call_results:

                try:
                    state.llm.new_messages.append(self.format_result(chunk, result))

                except json.JSONDecodeError as e:
                    e.add_note(f"Unable to JSON encode result for function {chunk.name} with arguments {chunk.arguments}")
                    raise e
            
            shared.llm.new_tool_call_results = []


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
    

class IntegrateMCPToolResultsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    async def __call__(self, state: T, shared: S) -> None:

        remaining: list[Tuple[AIChunkToolCall, Any]] = []


        async with shared.lock:

            for chunk, result in shared.llm.new_tool_call_results:

                if not isinstance(result, fastmcp.client.client.CallToolResult):
                        remaining.append((chunk, result))
                        continue

                try:
                    state.llm.new_messages.append(self.format_result(chunk, result))

                except json.JSONDecodeError as e:
                    e.add_note(f"Unable to JSON encode result for function {chunk.name} with arguments {chunk.arguments}")
                    raise e
            
            shared.llm.new_tool_call_results = remaining


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
