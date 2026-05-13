import discord
import edgygraph
from llmir import AIChunkText, AIChunkImageURL, AIChunks

from ...core.states import StateProtocol, SharedProtocol

class BuildDiscordEmbedNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):
    """Build a text chunk from the embed of a message."""

    required_packages = {"py-cord", "llmir"}

    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            message: discord.Message | None = shared.discord.messages[0] if shared.discord.messages else None

            if not message:
                raise ValueError("No messages in state to build embed chunk from.")
            if not state.llm.new_messages:
                raise ValueError("No AI messages in state to add embed chunk to.")
            
            for embed in message.embeds:
                state.llm.new_messages[-1].chunks.extend(self.format_embed(embed))
                

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