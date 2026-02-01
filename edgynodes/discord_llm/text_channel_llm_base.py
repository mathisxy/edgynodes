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

            if msg.attachments:
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
        text_message: Message | None = None
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
                        if text_message is None:
                            text_message = await channel.send(content=text)
                        else:
                            await text_message.edit(content=text)
                        last_edit = now

                else:
                    await cls.send_chunk(chunk, channel)
                    chunks.append(chunk)


        if text_message:
            await text_message.edit(content=text)
            chunks.append(
                AIChunkText(
                    text=text
                )
            )

        return chunks


    @classmethod
    async def send_chunk(cls, chunk: AIChunks, channel: Messageable) -> Message:

        match chunk:
            case AIChunkText():
                return await channel.send(content=chunk.text)
            case AIChunkFile():
                file = discord.File(io.BytesIO(chunk.bytes), filename=chunk.name)
                return await channel.send(file=file)
            case AIChunkImageURL():
                return await channel.send(content=chunk.url)
            case AIChunkToolCall():
                return await channel.send(embed=discord.Embed(title=chunk.name, description="\n".join([f" - {k}: {v}" for k, v in chunk.arguments.items()])))
            case _:
                raise ValueError(f"Unknown chunk type: {chunk}")
    