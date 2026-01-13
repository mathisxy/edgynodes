from edgygraph import GraphState
from llm_ir import AIMessage

class LLMGraphState(GraphState):
    messages: list[AIMessage] = []