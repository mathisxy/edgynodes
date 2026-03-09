from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol

class IncrementTurnCounterNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        state.llm.turn_count += 1
