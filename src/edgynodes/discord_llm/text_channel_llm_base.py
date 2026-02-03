from edgygraph import Node, Stream
from edgynodes.llm import LLMState, LLMShared
from edgynodes.discord import DiscordState, DiscordShared

from llmir import AIMessage, AIRoles, AIChunks, AIChunkFile, AIChunkText, AIChunkImageURL, AIMessageToolResponse, AIChunkToolCall
from discord.abc import Messageable
from discord import Message

import mimetypes
import discord
import io
import time


### STATE, SHARED

class DiscordLLMState(LLMState, DiscordState):
    pass

class DiscordLLMShared(LLMShared, DiscordShared):
    pass


### NODES

class BuildChatNode(Node[DiscordLLMState, DiscordLLMShared]):

    include_embeds: bool
    include_attachments: bool

    def __init__(self, include_embeds: bool = True, include_attachments: bool = True) -> None:
        super().__init__()
        self.include_embeds = include_embeds
        self.include_attachments = include_attachments


    async def run(self, state: DiscordLLMState, shared: DiscordLLMShared) -> None:

        chat: list[AIMessage] = []

        async with shared.lock:
            channel = shared.discord_message.channel
            bot = shared.discord_bot

        async for msg in channel.history(limit=20, oldest_first=False):

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

        state.llm_messages.extend(chat)


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

        if embed.image.url:
            chunks.append(AIChunkImageURL(url=embed.image.url))

        if embed.video.url: # Not supported currently
            chunks.append(AIChunkText(text=embed.video.url))
        
        return chunks


class RespondNode(Node[DiscordLLMState, DiscordLLMShared]):
    
    async def run(self, state: DiscordLLMState, shared: DiscordLLMShared) -> None:

        async with shared.lock:
            channel = shared.discord_message.channel
        
        for message in state.llm_new_messages:                
            
            for chunk in message.chunks:

                if isinstance(message, AIMessageToolResponse) and isinstance(chunk, AIChunkText):
                    continue # Send only non-text tool responses in the chat

                await self.send_chunk(chunk, channel)

        async with shared.lock:

            stream = shared.llm_stream

        
        if stream:
            streamed_chunks = await self.stream_response(stream, channel)

            state.llm_new_messages.append(
                AIMessage(
                    role=AIRoles.MODEL,
                    chunks=streamed_chunks
                )
            )

            async with shared.lock:

                shared.llm_stream = None


    @classmethod
    async def stream_response(cls, stream: Stream[AIChunks], channel: Messageable) -> list[AIChunks]:

        chunks: list[AIChunks] = []
        text_messages: list[Message] = []
        text: str = ""
        last_edit: float = 0.0
        EDIT_INTERVAL: float = 1.0

        async with stream:

            last_edit = time.monotonic()

            async for chunk in stream:

                print(f"LLM STREAM CHUNK: {chunk}")

                if isinstance(chunk, AIChunkText):

                    text += chunk.text
                    now = time.monotonic()

                    if now - last_edit >= EDIT_INTERVAL:
                        text_messages = await cls.send_text_chunks(text_messages, text, channel)
                        last_edit = now

                else:
                    await cls.send_chunk(chunk, channel)
                    chunks.append(chunk)

        if text.strip():
            await cls.send_text_chunks(text_messages, text, channel)
            for text_chunk in cls.chunk_string(text):
                chunks.append(
                    AIChunkText(
                        text=text_chunk
                    )
                )

        return chunks

    @classmethod
    async def send_text_chunks(cls, text_messages: list[Message], text: str, channel: Messageable) -> list[Message]:

        text_messages = text_messages.copy()

        for index, text_chunk in enumerate(cls.chunk_string(text)):

            if len(text_messages) > index:

                await text_messages[index].edit(content=text_chunk)

            else:

                text_messages.append(
                    await channel.send(content=text_chunk)
                )

        return text_messages




    @classmethod
    async def send_chunk(cls, chunk: AIChunks, channel: Messageable) -> list[Message]:

        match chunk:
            case AIChunkText():
                msgs: list[Message] = []
                for text_chunk in cls.chunk_string(chunk.text):
                    msgs.append(await channel.send(content=text_chunk))
                return msgs
            case AIChunkFile():
                file = discord.File(io.BytesIO(chunk.bytes), filename=chunk.name)
                return [await channel.send(file=file)]
            case AIChunkImageURL():
                return [await channel.send(content=chunk.url)]
            case AIChunkToolCall():
                formatted_args: dict[str, object] = {k.replace("_", " ").capitalize(): v for k, v in chunk.arguments.items()}
                embed = discord.Embed(title=chunk.name.replace("_", " ").title())
                for key, value in formatted_args.items():
                    embed.add_field(name=key, value=value, inline=True)
                return [await channel.send(embed=embed)]
            case _:
                raise ValueError(f"Unknown chunk type: {chunk}")
            

    @classmethod
    def chunk_string(cls, text: str, chunk_size: int = 2000):
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]