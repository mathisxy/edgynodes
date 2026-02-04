from typing import AsyncIterator, TypedDict
from types import TracebackType
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from llmir import AIChunkText, AIChunks, AIChunkToolCall
import json
from rich import print as rprint

from edgynodes.llm.core.streams import LLMStream # type: ignore


class ToolCallDict(TypedDict):
    id: str
    name: str
    arguments: str


class OpenAIStream(LLMStream):

    iterator: AsyncIterator[ChatCompletionChunk]

    _tool_calls: dict[int, ToolCallDict]

    def __init__(self, iterator: AsyncIterator[ChatCompletionChunk]) -> None:
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

                # Return next remaining tool call if any
                if self._tool_calls:
                    lowest_index = min(self._tool_calls)
                    tool_call_dict = self._tool_calls.pop(lowest_index)

                    try:
                        arguments = json.loads(tool_call_dict["arguments"])
                    except json.JSONDecodeError as e:
                        e.add_note(f"Tried to parse: {tool_call_dict["arguments"]}")
                        raise e


                    return AIChunkToolCall(
                        id=tool_call_dict["id"],
                        name=tool_call_dict["name"],
                        arguments=arguments,
                    )

                raise StopAsyncIteration
            
            delta = chunk.choices[0].delta

            if delta.content:
                formatted = AIChunkText(
                    text=delta.content
                )
            
                
            if delta.tool_calls:
                rprint("Received tool call delta: ", delta.tool_calls)
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
            
            elif tool_call.id and self._tool_calls[tool_call.index]["id"] and self._tool_calls[tool_call.index]["id"] != tool_call.id:
                raise ValueError(f"Conflicting tool call ids for index {tool_call.index}: {self._tool_calls[tool_call.index]['id']} and {tool_call.id}")

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
        