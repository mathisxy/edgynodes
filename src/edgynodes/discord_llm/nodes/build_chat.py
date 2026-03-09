from edgygraph import Node
from llmir import AIMessage, AIChunks, AIChunkText, AIChunkFile, AIChunkImageURL, AIRoles
import discord
import mimetypes

from ..core.states import StateProtocol, SharedProtocol

class BuildChatNode(Node[StateProtocol, SharedProtocol]):
    """Add the last `limit` messages in the discord channel to the messages in the state.

    Attributes:
        limit: The number of messages to load from the discord channel.
        include_embeds: Whether to transfer embeds to the messages.
        include_attachments: Whether to transfer attachments to the messages.
    """

    limit: int
    include_embeds: bool
    include_attachments: bool

    def __init__(self, limit: int = 20, include_embeds: bool = True, include_attachments: bool = True) -> None:

        self.limit = limit
        self.include_embeds = include_embeds
        self.include_attachments = include_attachments


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        chat: list[AIMessage] = []

        async with shared.lock:
            channel = shared.discord.text_channel
            bot = shared.discord.bot

        async for msg in channel.history(limit=self.limit, oldest_first=False):

            role = AIRoles.MODEL if msg.author == bot.user else AIRoles.USER

            chunks: list[AIChunks] = []

            if msg.content:
                chunks.append(AIChunkText(text=msg.content))

            if msg.embeds and self.include_embeds:
                for embed in msg.embeds:
                    chunks.extend(self.format_embed(embed))

            if msg.attachments and self.include_attachments:
                for attachment in msg.attachments:

                    mimetype, _ = mimetypes.guess_type(attachment.filename)
                    file_bytes = await attachment.read()

                    chunks.append(AIChunkFile(
                        name=attachment.filename,
                        mimetype=str(mimetype),
                        bytes=file_bytes,
                    ))

            chat.append(AIMessage(
                role=role,
                chunks=chunks,
            ))

        chat.reverse()

        state.llm.messages.extend(chat)


    def format_embed(self, embed: discord.Embed) -> list[AIChunks]:
        """Konvertiert ein Discord Embed in Text AI Chunks"""
        chunks: list[AIChunks] = []
        
        if embed.title:
            chunks.append(AIChunkText(text=f"**{embed.title}**"))
        
        if embed.description:
            chunks.append(AIChunkText(text=embed.description))
        
        if embed.fields:
            for field in embed.fields:
                chunks.append(AIChunkText(text=f"{field.name}: {field.value}"))
        
        if embed.footer and embed.footer.text:
            chunks.append(AIChunkText(text=f"__{embed.footer.text}__"))

        if embed.image:
            chunks.append(AIChunkImageURL(url=embed.image.url))

        if embed.video: # Not supported currently
            chunks.append(AIChunkText(text=embed.video.url))
        
        return chunks

        