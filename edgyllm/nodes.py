from edgygraph import GraphNode
from .states import LLMGraphState

class LLMNode(GraphNode[LLMGraphState]):

    model: str
    
    def __init__(self, model: str) -> None:
        self.model = model