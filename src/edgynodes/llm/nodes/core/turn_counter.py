from edgygraph import Node

from ...states import StateProtocol, SharedProtocol

class TurnCounterNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        state.llm.turn_count += 1
