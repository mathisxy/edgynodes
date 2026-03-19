from llmir import AIMessages, AIMessage, AIChunkText, AIChunkImageURL, AIChunks, AIRoles, AITool, AIChunkToolCall
from llmir.adapter import OpenAIAdapter
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionFunctionToolParam, ChatCompletion, ChatCompletionMessageParam
import json
import requests
import base64

from ...core.states import StateProtocol, SharedProtocol
from ...core.nodes import LLMNode
from .utils.streams import OpenAIStream



class LLMOpenAINode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](LLMNode[T, S]):

    dependencies = {"llmir", "openai"}

    client: AsyncOpenAI
    extra_body: dict[str, object] | None

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1", stream: bool = False, extra_body: dict[str, object] | None = None) -> None:
        super().__init__(model, stream)

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.extra_body = extra_body


    async def __call__(self, state: T, shared: S) -> None:
        
        chat = state.llm.messages

        if not self.stream:

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=self.format_messages(chat),
                tools=self.format_tools(state.llm.tools),
                extra_body=self.extra_body,
            )

            state.llm.new_messages.append(
                self.format_response(state, response)
            )
            

        else:

            assert self.supports.streaming == True

            stream: AsyncStream[ChatCompletionChunk] = await self.client.chat.completions.create(
                model=self.model,
                messages=self.format_messages(chat),
                tools=self.format_tools(state.llm.tools),
                stream=True
            )

            async with shared.lock:
                if shared.llm.stream is not None:
                    raise Exception("Stream variable in Shared is occupied")
            
                shared.llm.stream = OpenAIStream(iterator=stream)


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
    
        

    def format_tools(self, tools: list[AITool]) -> list[ChatCompletionFunctionToolParam]:

        return OpenAIAdapter.tools(tools)

    
    def format_messages(self, messages: list[AIMessages]) -> list[ChatCompletionMessageParam]:

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

        formatted = OpenAIAdapter.chat(messages)
        # rprint(formatted)
        return formatted