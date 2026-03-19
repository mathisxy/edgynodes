from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol
from ..core.supports import Supports

class LLMNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    def __init__(self, model: str, streaming: bool = False) -> None:
        super().__init__()

        self.model = model
        self.stream = streaming

        self.supports: Supports = Supports()