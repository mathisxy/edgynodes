from collections.abc import Sequence
import requests
import base64
from ollama import (
    AsyncClient,
    Image,
    ChatResponse,
)
from llmir import AIMessage, AIRoles, AIChunkToolCall, AIChunkText, AIChunks
from llmir.adapter import OllamaAdapter

from edgynodes.llm.core.states import SharedProtocol, StateProtocol # type: ignore

from ...core.nodes import LLMNode
from .utils.streams import OllamaStream

class LLMOllamaNode(LLMNode):

    def __init__(self, model: str, stream: bool = False, keep_alive: str | None = None) -> None:
        super().__init__(model, stream)
        self.keep_alive = keep_alive
    
    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        chat = OllamaAdapter.chat(state.llm.messages)
        tools = OllamaAdapter.tools(state.llm.tools)

        for message in chat:
            if message.images:
                message.images = await self.download_remote_image_urls(message.images)

        print(chat)
        
        response = await AsyncClient().chat( # type: ignore
            model=self.model,
            stream=self.stream,
            keep_alive=self.keep_alive,
            messages=chat,
            tools=tools,
        )

        if isinstance(response, ChatResponse):

            text = response.message.content
            tool_calls = response.message.tool_calls

            chunks: list[AIChunks] = []

            if text:
                chunks.append(
                    AIChunkText(
                        text=text
                    )
                )
            if tool_calls:
                for tool_call in tool_calls:
                    chunks.append(
                        AIChunkToolCall(
                            id=tool_call.function.name,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )
                    
            if not chunks:
                raise ValueError("No chunks were generated from the response.")

            state.llm.new_messages.append(
                AIMessage(
                    role=AIRoles.MODEL,
                    chunks=chunks,
                )
            )
        
        else:

            async with shared.lock:
                shared.llm.stream = OllamaStream(response)






    async def download_remote_image_urls(self, images: Sequence[Image]) -> None:

        for image in images:

            if isinstance(image.value, str) and image.value.startswith("http"):
                response = requests.get(image.value)
                image.value = f"data:image/jpeg;base64,{base64.b64encode(response.content).decode('utf-8')}"