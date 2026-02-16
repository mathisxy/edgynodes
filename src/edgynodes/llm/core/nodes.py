from edgygraph import Node
from llmir import AIMessages
from pydantic import BaseModel
from ..states import StateProtocol, SharedProtocol


class Supports(BaseModel):

    vision: bool = True
    audio: bool = False
    streaming: bool = True
    remote_image_urls: bool = True


class LLMNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    model: str
    enable_streaming: bool = False

    supports: Supports = Supports()

    def __init__(self, model: str, enable_streaming: bool = False) -> None:
        super().__init__()

        self.model = model
        self.enable_streaming=enable_streaming



class AddMessageNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    message: AIMessages

    def __init__(self, message: AIMessages) -> None:
        super().__init__()

        self.message = message

    async def __call__(self, state: T, shared: S) -> None:
    
        state.llm.messages.append(
            self.message
        )


class SaveNewMessagesNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    async def __call__(self, state: T, shared: S) -> None:

        print("Saving new messages to messages")
        
        state.llm.messages.extend(state.llm.new_messages)

        state.llm.new_messages = []