from typing import Callable
import discord
import asyncio

from edgygraph import Node

from ...core.states import StateProtocol, SharedProtocol

class StartRecordVoiceNode(Node[StateProtocol, SharedProtocol]):

    sink_factory: Callable[..., discord.sinks.Sink]
    delay: float

    def __init__(self, sink_factory: Callable[..., discord.sinks.Sink] | None = None, delay: float = 0) -> None:
        
        self.sink_factory = sink_factory or (lambda: discord.sinks.WaveSink())
        self.delay = delay

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        sink = self.sink_factory()

        async with shared.lock:
            voice_client = shared.discordvoice.client
            finished_flag = shared.discordvoice.recording_finished

            shared.discordvoice.sink = sink

        
        if not voice_client:
            raise Exception("Need to be in a voice channel to start recording.")
        
        finished_flag.clear()

        async def on_done(sink: discord.sinks.Sink):
            finished_flag.set()

        if self.delay:
            await asyncio.sleep(self.delay)

        voice_client.start_recording( # type: ignore
            sink,  # The sink to use.
            on_done,
        )

class StopRecordVoiceNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            voice_client = shared.discordvoice.client
            finished_flag = shared.discordvoice.recording_finished

        if not voice_client:
            raise Exception("Need to be in a voice channel to stop recording.")
        
        voice_client.stop_recording()

        await finished_flag.wait()


class AwaitRecordVoiceStopNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        async with shared.lock:
            finished_flag = shared.discordvoice.recording_finished

        await finished_flag.wait()

        print("Recording finished!")
