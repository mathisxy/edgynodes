from edgygraph import Node, State, Shared, Stream
from llmir import AIMessages, Tool, AIChunkToolCall, AIChunks
from pydantic import BaseModel, Field
from typing import Callable, Any, Tuple
import asyncio

class LLMStream(Stream[AIChunks]):
    abort: asyncio.Event

    def __init__(self) -> None:
        self.abort = asyncio.Event()

class LLMState(State):
    llm_messages: list[AIMessages] = Field(default_factory=list[AIMessages])
    llm_new_messages: list[AIMessages] = Field(default_factory=list[AIMessages])

    llm_tools: list[Tool] = Field(default_factory=list[Tool])


class LLMShared(Shared):
    llm_stream: LLMStream | None = None

    llm_tool_functions: dict[str, Callable[..., Any]] = Field(default_factory=dict[str, Callable[..., Any]]) # name -> function

    llm_new_tool_calls: list[AIChunkToolCall] = Field(default_factory=list[AIChunkToolCall])
    llm_new_tool_call_results: list[Tuple[AIChunkToolCall, Any]] = Field(default_factory=list[Tuple[AIChunkToolCall, Any]])
    


class Supports(BaseModel):

    vision: bool = True
    audio: bool = False
    streaming: bool = True
    remote_image_urls: bool = True


class LLMNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    model: str
    enable_streaming: bool = False

    supports: Supports = Supports()

    def __init__(self, model: str, enable_streaming: bool = False) -> None:
        super().__init__()

        self.model = model
        self.enable_streaming=enable_streaming



class AddMessageNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    message: AIMessages

    def __init__(self, message: AIMessages) -> None:
        super().__init__()

        self.message = message

    async def run(self, state: T, shared: S) -> None:
    
        state.llm_messages.append(
            self.message
        )


class SaveNewMessagesNode[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    async def run(self, state: T, shared: S) -> None:

        print("Saving new messages to messages")
        
        state.llm_messages.extend(state.llm_new_messages)

        state.llm_new_messages = []