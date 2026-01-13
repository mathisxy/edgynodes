from .nodes import LLMNode
from .states import LLMGraphState

from mistralai import Mistral

from llm_ir import AIMessage, AIRoles, AIChunkText
from llm_ir.adapter import to_openai

class LLMNodeMistral(LLMNode):

    client: Mistral

    def __init__(self, model: str, api_key: str) -> None:
        super().__init__(model)

        self.client = Mistral(api_key=api_key)


    def run(self, state: LLMGraphState) -> LLMGraphState:
        
        history = state.messages

        print(history)

        response = self.client.chat.complete(
            model=self.model,
            messages=to_openai(history),
        )

        print(response)

        state.messages.append(
            AIMessage(
                role=AIRoles.MODEL,
                chunks=[AIChunkText(
                    content=response.choices[0].message.content
                    )],
            )
        )

        return state
    