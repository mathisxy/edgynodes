from edgygraph import Node
from llmir import AIMessages
from pydantic import BaseModel
from .states import LLMState, LLMShared    


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