import edgygraph
import discord
import mimetypes
from llmir import AIChunkFile

from ...core.states import StateProtocol, SharedProtocol

class BuildDiscordAttachmentsNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    """Build file chunks from the attachments of a message."""

    required_packages = {"py-cord", "llmir", "mimetypes"}

    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            message: discord.Message | None = shared.discord.messages[0] if shared.discord.messages else None

            if not message:
                raise ValueError("No messages in state to build attachments from.")
            if not state.llm.new_messages:
                raise ValueError("No AI messages in state to add attachments to.")
            
            for attachment in message.attachments:

                mimetype, _ = mimetypes.guess_type(attachment.filename)
                file_bytes = await attachment.read()

                state.llm.new_messages[-1].chunks.append(AIChunkFile(
                    name=attachment.filename,
                    mimetype=str(mimetype),
                    bytes=file_bytes,
                ))