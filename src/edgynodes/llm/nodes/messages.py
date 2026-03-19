from llmir import AIMessages
from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol

class AddMessageNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    dependencies = {"llmir"}

    message: AIMessages

    def __init__(self, message: AIMessages) -> None:
        super().__init__()

        self.message = message

    async def __call__(self, state: T, shared: S) -> None:
    
        state.llm.messages.append(
            self.message
        )


class SaveNewMessagesNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    dependencies = {"llmir"}

    async def __call__(self, state: T, shared: S) -> None:
        
        state.llm.messages.extend(state.llm.new_messages)

        state.llm.new_messages = []