from edgygraph import Node

from ...states import StateProtocol, SharedProtocol
from .utils.supports import Supports

class LLMNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](Node[T, S]):

    model: str
    enable_streaming: bool = False

    supports: Supports = Supports()

    def __init__(self, model: str, enable_streaming: bool = False) -> None:
        self.model = model
        self.enable_streaming=enable_streaming