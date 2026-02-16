from edgygraph import Node, Stream
from discord.abc import Messageable
from discord import Message
from llmir import AIMessage, AIChunks, AIChunkText, AIChunkFile, AIChunkImageURL, AIMessageToolResponse, AIChunkToolCall, AIRoles
from typing import Literal, Generator
import discord
import mimetypes
import io
import time

from ..states import StateProtocol, SharedProtocol

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


class RespondNode(Node[StateProtocol, SharedProtocol]):
    """Send all new messages in the state to the Discord channel.

    This node also streams the response from the LLM, if the stream is set in the shared state.
    The streamed response is added to the new messages in the state.
    The stream is then set to None in the shared state.

    Chunks from tool responses are handled according to the `send_tool_responses` parameter.

    Attributes:
        send_tool_responses: Whether to send tool responses in the Discord channel.
            - `True`: Send all tool responses.
            - `False`: Do not send any tool responses.
            - `"only_media"`: Only send **non text chunks** in tool responses.
        stream_text_edit_interval: The interval in seconds to update the streamed message in the Discord channel.
    """

    send_tool_responses: Literal[True, False, "only_media"]
    stream_text_edit_interval: float


    def __init__(self, send_tool_responses: Literal[True, False, "only_media"] = "only_media", stream_text_edit_interval: float = 1.0) -> None:
        
        self.send_tool_responses = send_tool_responses
        self.stream_text_edit_interval = stream_text_edit_interval

    
    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            channel = shared.discord.text_channel
        
        for message in state.llm.new_messages:                
            
            for chunk in message.chunks:

                if isinstance(message, AIMessageToolResponse):
                    if not self.send_tool_responses or (self.send_tool_responses == "only_media" and isinstance(chunk, AIChunkText)):
                        continue

                await self.send_chunk(chunk, channel)

        async with shared.lock:

            stream = shared.llm.stream

        
        if stream:
            streamed_chunks = await self.stream_response(stream, channel, self.stream_text_edit_interval)

            state.llm.new_messages.append(
                AIMessage(
                    role=AIRoles.MODEL,
                    chunks=streamed_chunks
                )
            )

            async with shared.lock:

                shared.llm.stream = None



    @classmethod
    async def stream_response(cls, stream: Stream[AIChunks], channel: Messageable, edit_interval: float) -> list[AIChunks]:
        """Stream the response from the LLM to the Discord channel.
        
        This method handles all AI chunk types.
        It sends text chunks as one text message that is edited incrementally. 
        The text message is only split at the maximum discord message length.

        Args:
            stream: The stream of AI chunks to be processed.
            channel: The Discord channel where the response will be sent.
            edit_interval: The interval in seconds at which the text message is edited.

        Returns:
            A list of all chunks that were streamed.
        """

        chunks: list[AIChunks] = []
        text_messages: list[Message] = []
        text: str = ""
        last_edit: float = 0.0

        async with stream:

            last_edit = time.monotonic()

            async for chunk in stream:

                if isinstance(chunk, AIChunkText):

                    text += chunk.text
                    now = time.monotonic()

                    if now - last_edit >= edit_interval:
                        text_messages = await cls.send_text_incremental(text_messages, text, channel)
                        last_edit = now

                else:
                    await cls.send_chunk(chunk, channel)
                    chunks.append(chunk)

        if text.strip():
            await cls.send_text_incremental(text_messages, text, channel)
            for text_chunk in cls.chunk_string(text):
                chunks.append(
                    AIChunkText(
                        text=text_chunk
                    )
                )

        return chunks



    @classmethod
    async def send_text_incremental(cls, text_messages: list[Message], text: str, channel: Messageable) -> list[Message]:
        """Send the text to the Discord channel by editing last Discord messages and creating new ones if needed.

        The text is assumed to be append-only and not modified elsewhere.

        The text is split into chunks of 2000 characters to fit the Discord message limit.
        The last message is edited to contain the last chunk of text.
        The messages before the last message are not edited to limit the number of API calls.

        Args:
            text_messages: The list of messages to edit.
            text: The text to send.
            channel: The Discord channel to send the text to.

        Returns:
            The list of messages that were edited or created.
        """

        text_messages = text_messages.copy()

        for index, text_chunk in enumerate(cls.chunk_string(text)):

            if index == len(text_messages) -1: # message is last message -> edit it

                await text_messages[index].edit(content=text_chunk)

            elif index >= len(text_messages): # out of bounds -> create new message

                text_messages.append(
                    await channel.send(content=text_chunk)
                )
            
            # else: message is not last message -> continue
                

        return text_messages



    @classmethod
    async def send_chunk(cls, chunk: AIChunks, channel: Messageable) -> list[Message]:
        """Send an AI chunk to the Discord channel.

        Args:
            chunk: The AI chunk to send.
            channel: The Discord channel to send the chunk to.

        Returns:
            The list of messages that were sent.
        """

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
                embed = cls.format_tool_call_chunk(chunk)
                return [await channel.send(embed=embed)]
            case _:
                raise ValueError(f"Unknown chunk type: {chunk}")
            


    @classmethod
    def chunk_string(cls, text: str, chunk_size: int = 2000) -> Generator[str]:
        """Split a string into chunks of a specified size.
        
        Args:
            text: The input string to be split.
            chunk_size: The maximum size of each chunk.

        Returns:
            A generator that yields each chunk of the input string.
        """

        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]

    

    @classmethod
    def format_tool_call_chunk(cls, chunk: AIChunkToolCall, inline: bool = True, max_value_length: int = 1024) -> discord.Embed:
        """Format a tool call chunk into a Discord embed.

        Args:
            chunk: The tool call chunk to be formatted.
            inline: Whether the fields in the embed should be inline.

        Returns:
            A Discord embed containing the information of the tool call.
        """
        
        formatted_args: dict[str, str] = {k.replace("_", " ").capitalize(): str(v) for k, v in chunk.arguments.items()}
        embed = discord.Embed(title=chunk.name.replace("_", " ").title())
        for key, value in formatted_args.items():
            value = value[:max_value_length - 4] + " ..." if len(value) > 1024 else value
            embed.add_field(name=key, value=value, inline=inline)

        return embed
