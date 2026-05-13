
import discord
import edgygraph
from llmir.chunks import AIChunkText

from ...core.states import StateProtocol, SharedProtocol


class BuildTextChunkNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):
    """Build a text chunk from the content of a message."""

    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            message: discord.Message | None = shared.discord.messages[0] if shared.discord.messages else None

            if not message:
                raise ValueError("No messages in state to build text chunk from.")
            if not state.llm.new_messages:
                raise ValueError("No AI messages in state to add text chunk to.")
            
            text = message.content

            state.llm.new_messages[-1].chunks.append(
                AIChunkText(text=text)
            )


