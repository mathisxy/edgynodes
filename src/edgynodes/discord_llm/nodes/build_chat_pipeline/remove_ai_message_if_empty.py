import edgygraph

from ...core.states import StateProtocol, SharedProtocol

class RemoveAIMessageIfEmptyNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):
    """
    Removes the last AI message from the new AI messages list if it has no chunks.
    """

    async def __call__(self, state: T, shared: S) -> None:

        if not state.llm.new_messages:
            raise ValueError("No AI messages in state to check for emptiness.")
        
        if not state.llm.new_messages[-1].chunks:
            state.llm.new_messages.pop()