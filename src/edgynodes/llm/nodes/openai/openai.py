from llmir import AIMessages, AIMessage, AIChunkText, AIChunkImageURL, AIChunks, AIRoles, Tool, AIChunkToolCall
from llmir.adapter import to_openai, OpenAIMessages
from typing import AsyncIterator
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk, ChatCompletionFunctionToolParam, ChatCompletion
import json
import requests
import base64

from ...states import StateProtocol, SharedProtocol
from ..core.llm import LLMNode
from .utils.streams import OpenAIStream



class LLMOpenAINode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](LLMNode[T, S]):

    client: AsyncOpenAI
    extra_body: dict[str, object] | None

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1", enable_streaming: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model, enable_streaming)

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.extra_body = extra_body


    async def __call__(self, state: T, shared: S) -> None:
        
        chat = state.llm.messages

        if not self.enable_streaming:

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=self.format_messages(chat), # type: ignore
                tools=self.format_tools(state.llm.tools),
                extra_body=self.extra_body,
            )

            state.llm.new_messages.append(
                self.format_response(state, response)
            )
            

        else:

            assert self.supports.streaming == True

            stream: AsyncIterator[ChatCompletionChunk] = await self.client.chat.completions.create( # type: ignore
                model=self.model,
                messages=self.format_messages(chat), # type: ignore
                tools=self.format_tools(state.llm.tools),
                stream=True
            )

            async with shared.lock:
                if shared.llm.stream is not None:
                    raise Exception("Stream variable in Shared is occupied")
            
                shared.llm.stream = OpenAIStream(iterator=stream) # type: ignore


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