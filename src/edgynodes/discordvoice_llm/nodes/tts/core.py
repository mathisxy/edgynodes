from abc import abstractmethod
import asyncio
import io

import discord
from edgygraph import Node
from llmir import AIRoles, AIChunkText, AIMessage

from ...core.states import StateProtocol, SharedProtocol
from ....discordvoice import InterruptException


class BaseTTSNode[T: StateProtocol, S: SharedProtocol](Node[StateProtocol, SharedProtocol]):
    """
    Abstract base for TTS nodes. Subclasses implement `synthesize_to_wav_bytes(text) -> bytes`.
    Handles all Discord playback, streaming logic, and interrupt handling.
    """

    dependencies: set[str] = {"py-cord", "llmir"}

    def __init__(self, min_stream_chunk_length: int = 20) -> None:
        self.min_stream_chunk_length = min_stream_chunk_length
        

    @abstractmethod
    async def generate_wav_bytes(self, text: str, interrupt: asyncio.Event) -> bytes:
        """Synthesize text to WAV bytes (PCM, standard wav container)."""
        ...

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            voice_client = shared.discordvoice.client
            interrupt = shared.discordvoice.interrupt
            stream = shared.llm.stream

        if voice_client is None:
            raise ValueError("No voice client found.")

        if interrupt.is_set():
            raise InterruptException("Playback interrupted before start")

        # Replay already-generated messages
        current_text = ""
        for message in state.llm.new_messages:
            if message.role == AIRoles.MODEL:
                for text in [chunk.text for chunk in message.chunks if isinstance(chunk, AIChunkText)]:
                    current_text += text

        try:
            audio = await self.tts(current_text, interrupt)
            await self.play(voice_client, audio, interrupt)

        except InterruptException:
            async with shared.lock:
                shared.llm.stream = None # Skip stream if exists
            raise

        if stream is None:
            return

        # Stream new messages
        queue: asyncio.Queue[discord.FFmpegPCMAudio | None] = asyncio.Queue(maxsize=1)
        completed: str = ""


        async def enqueue(text: str):
            nonlocal queue
            nonlocal completed
            audio = await self.tts(text, interrupt)
            await queue.put(audio)
            completed += text


        async def producer():
            nonlocal state
            nonlocal completed
                
            async with stream:

                try:
                    pending = ""
                    
                    async for chunk in stream:
                        if isinstance(chunk, AIChunkText):
                            pending += chunk.text

                            while pending:
                                complete, pending = self.extract_complete_lines(pending, min_chars=self.min_stream_chunk_length)

                                if not complete:
                                    break
                                
                                await enqueue(complete)

                    
                    while pending:
                        complete, pending = self.extract_complete_lines(pending, min_chars=self.min_stream_chunk_length)

                        if not complete:
                            complete = pending
                            pending = ""

                        await enqueue(complete)
                
                finally:
                    state.llm.new_messages.append(
                        AIMessage(
                            role=AIRoles.MODEL,
                            chunks=[AIChunkText(text=completed)]
                        )
                    )
                    
                    await queue.put(None)


        async def consumer():
            while (audio := await queue.get()) is not None:
                await self.play(voice_client, audio, interrupt)

        try:

            producer_task = producer()
            consumer_task = consumer()

            try:
                await producer_task
            finally:
                await queue.put(None)
                await consumer_task

        finally:
            async with shared.lock:
                shared.llm.stream = None



    async def tts(self, text: str, interrupt: asyncio.Event) -> discord.FFmpegPCMAudio:
        if not text:
            raise ValueError("Text is empty")

        wav_bytes = await self.generate_wav_bytes(text, interrupt)

        if interrupt.is_set():
            raise InterruptException("Voice generation interrupted")

        audio_buffer = io.BytesIO(wav_bytes)
        return discord.FFmpegPCMAudio(
            audio_buffer,
            pipe=True,
            before_options='-f wav',
            options='-af afade=t=in:st=0:d=0.01',
        )


    @classmethod
    async def play(
        cls,
        voice_client: discord.VoiceClient,
        audio_source: discord.AudioSource,
        interrupt_event: asyncio.Event,
    ):
        play_future = voice_client.play(audio_source, wait_finish=True)  # type: ignore

        await asyncio.wait(
            [
                play_future,
                asyncio.create_task(interrupt_event.wait()),  # type: ignore
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if interrupt_event.is_set():
            voice_client.stop()
            raise InterruptException("Playback interrupted")

    @classmethod
    def extract_complete_lines(cls, text: str, min_chars: int = 10):
        last_newline = text.rfind('\n')
        if last_newline == -1:
            return None, text
        if last_newline >= min_chars:
            complete = text[:last_newline]
            remaining = text[last_newline + 1:]
            return complete, remaining
        return None, text