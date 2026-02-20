from llmir import AIMessages
from edgygraph import Node

from ...states import StateProtocol, SharedProtocol

class AddMessageNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    message: AIMessages

    def __init__(self, message: AIMessages) -> None:

        self.message = message

    async def __call__(self, state: T, shared: S) -> None:
    
        state.llm.messages.append(
            self.message
        )


class SaveNewMessagesNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    async def __call__(self, state: T, shared: S) -> None:
        
        state.llm.messages.extend(state.llm.new_messages)

        state.llm.new_messages = []