from edgygraph import Node, State, Shared, Stream
from llm_ir import AIMessage
from pydantic import BaseModel, Field
import asyncio

class LLMStream(Stream[str]):
    abort: asyncio.Event

    def __init__(self) -> None:
        self.abort = asyncio.Event()

class LLMState(State):
    messages: list[AIMessage] = Field(default_factory=list[AIMessage])
    new_messages: list[AIMessage] = Field(default_factory=list[AIMessage])

class LLMShared(Shared):
    llm_stream: LLMStream | None = None
    pass


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

    message: AIMessage

    def __init__(self, message: AIMessage) -> None:
        super().__init__()

        self.message = message

    async def run(self, state: T, shared: S) -> None:
        await super().run(state, shared)
    
        state.messages.append(
            self.message
        )


class SaveNewMessages[T: LLMState = LLMState, S: LLMShared = LLMShared](Node[T, S]):

    async def run(self, state: T, shared: S) -> None:
        
        state.messages.extend(state.new_messages)

        state.new_messages = []