from types import TracebackType
from .base import LLMNode, LLMState, LLMShared, LLMStream

from openai import AsyncOpenAI as OpenAI
from openai.types.chat import ChatCompletionChunk, ChatCompletionFunctionToolParam, ChatCompletion
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

from typing import AsyncIterator, AsyncGenerator, TypedDict

from llmir import AIMessages, AIRoles, AIChunkText, AIChunkImageURL, Tool, AIChunks, AIChunkToolCall, AIMessage
from llmir.adapter import to_openai, OpenAIMessages
from rich import print as rprint
import requests
import base64
import json

class ToolCallDict(TypedDict):
    id: str
    name: str
    arguments: str


class OpenAIStream(LLMStream):

    iterator: AsyncGenerator[ChatCompletionChunk]

    _tool_calls: dict[int, ToolCallDict]

    def __init__(self, iterator: AsyncGenerator[ChatCompletionChunk]) -> None:
        super().__init__() 
        
        self.iterator = iterator

        self._tool_calls = {}

    async def __anext__(self) -> AIChunks:

        if self.abort.is_set():
            print("Aborting Stream")
            raise StopAsyncIteration

        formatted: AIChunks | None = None

        chunk: ChatCompletionChunk

        while not formatted:
            
            try:
                chunk = await self.iterator.__anext__()
            
            except StopAsyncIteration:

                if self._tool_calls:
                    lowest_index = min(self._tool_calls)
                    tool_call_dict = self._tool_calls.pop(lowest_index)

                    return AIChunkToolCall(
                        id=tool_call_dict["id"],
                        name=tool_call_dict["name"],
                        arguments=json.loads(tool_call_dict["arguments"])
                    )

                raise StopAsyncIteration
            
            delta = chunk.choices[0].delta

            if delta.content and delta.content.strip():
                formatted = AIChunkText(
                    text=delta.content
                )
            
                
            if delta.tool_calls:
                self.integrate_tool_calls(delta.tool_calls)

                        
                
        return formatted
    

    def integrate_tool_calls(self, tool_calls: list[ChoiceDeltaToolCall]) -> None:

        for tool_call in tool_calls:

                    if tool_call.index not in self._tool_calls:
                        
                        self._tool_calls[tool_call.index] = ToolCallDict(
                            id="",
                            name="",
                            arguments="",
                        )

                    if tool_call.id:
                        self._tool_calls[tool_call.index]["id"] = tool_call.id

                    if function := tool_call.function:

                        if function.name:
                            self._tool_calls[tool_call.index]["name"] = function.name

                        if function.arguments:
                            self._tool_calls[tool_call.index]["arguments"] += function.arguments


        
    
    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        return await super().__aexit__(exc_type, exc, tb)
    
    async def aclose(self) -> None:
        await super().aclose()
        await self.iterator.close() # type:ignore 
        print("aclose called")
        pass
        

class LLMNodeOpenAI[T: LLMState = LLMState, S: LLMShared = LLMShared](LLMNode[T, S]):

    client: OpenAI  

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1", enable_streaming: bool = False) -> None:
        super().__init__(model, enable_streaming)

        self.client = OpenAI(api_key=api_key, base_url=base_url)


    async def run(self, state: T, shared: S) -> None:
        
        chat = state.llm_messages

        # printable_history = [message for message in history if not any(isinstance(chunk, AIChunkImageURL) for chunk in message.chunks)]
        # print(printable_history)

        if not self.enable_streaming:

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.format_messages(chat), # type: ignore
                tools=self.format_tools(state.llm_tools),
            )

            # print(response.choices[0].message.content)

            state.llm_new_messages.append(
                self.format_response(state, response)
            )
            

        else:

            assert self.supports.streaming == True

            stream: AsyncIterator[ChatCompletionChunk] = await self.client.chat.completions.create( # type: ignore
                model=self.model,
                messages=self.format_messages(chat), # type: ignore
                tools=self.format_tools(state.llm_tools),
                stream=True
            )

            async with shared.lock:
                if shared.llm_stream is not None:
                    raise Exception("Stream variable in Shared is occupied")
            
                shared.llm_stream = OpenAIStream(iterator=stream) # type: ignore


    def format_response(self, state: T, response: ChatCompletion):

        chunks: list[AIChunks] = []

        if tool_calls := response.choices[0].message.tool_calls:
            for tool_call in tool_calls:
                chunks.append(
                    AIChunkToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name, #type:ignore
                        arguments=json.loads(tool_call.function.arguments)#type:ignore
                    )
                )
        
        if text := response.choices[0].message.content:
            chunks.append(
                AIChunkText(
                    text=text
                )
            )
        
        return AIMessage(
            role=AIRoles.MODEL,
            chunks=chunks
        )
    
        

    def format_tools(self, tools: list[Tool]) -> list[ChatCompletionFunctionToolParam]:

        formatted_tools: list[ChatCompletionFunctionToolParam] = []

        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            })

        return formatted_tools

    
    def format_messages(self, messages: list[AIMessages]) -> list[OpenAIMessages]:

        if not self.supports.remote_image_urls:

            for msg in messages:
                if isinstance(msg, AIMessage):
                    for chunk in msg.chunks:
                        if isinstance(chunk, AIChunkImageURL) and chunk.url.strip().startswith("http"):
                            try:
                                response = requests.get(chunk.url)
                                # print(len(response.content))
                                response.raise_for_status()
                                image_data = response.content
                                mime_type = response.headers.get('content-type', '')
                                if not mime_type:
                                    raise ValueError("Unknown MIME type")
                                # print(mime_type)
                                base64_data = base64.b64encode(image_data).decode('utf-8')
                                chunk.url = f"data:{mime_type};base64,{base64_data}"
                            except Exception as e:
                                print(f"Error downloading image from URL {chunk.url}: {e}")

        formatted = to_openai(messages)
        # rprint(formatted)
        return formatted