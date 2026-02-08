from edgygraph import Node
from llmir import AIMessage, AIRoles, AIChunkText
from rich import print

from ..states import State, Shared

class TranscriptionsToAINode(Node[State, Shared]):


    async def run(self, state: State, shared: Shared) -> None:
        
        for user_id, transcription in state.discordvoice.transcriptions.items():
            
            if transcription.strip() == "":
                continue

            state.llm.new_messages.append(
                AIMessage(
                    role=AIRoles.USER,
                    chunks=[AIChunkText(text=transcription)]
                )
            )

        state.discordvoice.transcriptions.clear()

        print(state)