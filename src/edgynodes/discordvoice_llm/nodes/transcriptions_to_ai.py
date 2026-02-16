from edgygraph import Node
from llmir import AIMessage, AIRoles, AIChunkText

from ..states import StateProtocol, SharedProtocol

class TranscriptionsToAINode(Node[StateProtocol, SharedProtocol]):


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        for user_id, transcription in state.discordvoice.transcriptions.items(): # type: ignore
            
            if transcription.strip() == "":
                continue

            state.llm.new_messages.append(
                AIMessage(
                    role=AIRoles.USER,
                    chunks=[AIChunkText(text=transcription)]
                )
            )

        state.discordvoice.transcriptions.clear()