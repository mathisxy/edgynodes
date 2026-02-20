from edgygraph import Node
from typing import Callable, Awaitable
import discord
import time
import asyncio

from ..states import StateProtocol, SharedProtocol
from ..utils.vad_wave_sink import VADWaveSink

from rich import print


class JoinVoiceChannelNode(Node[StateProtocol, SharedProtocol]):


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            voice_channel = shared.discordvoice.channel
            voice_client = shared.discordvoice.client

        if voice_client and voice_client.is_connected():
            if voice_client.channel != voice_channel:
                # Im falschen Channel -> umziehen
                await voice_client.move_to(voice_channel)
        
        else:
            # Nicht verbunden -> neu connecten
            new_voice_client = await voice_channel.connect()
            
            async with shared.lock:
                shared.discordvoice.client = new_voice_client
            

class LeaveVoiceChannelNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        async with shared.lock:
            voice_client = shared.discordvoice.client

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        async with shared.lock:
            shared.discordvoice.client = None



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


class AwaitVoiceStartVADNode(Node[StateProtocol, SharedProtocol]):

    on_finished: Callable[[StateProtocol, SharedProtocol], Awaitable[None]] | None

    def __init__(self, on_finished: Callable[[StateProtocol, SharedProtocol], Awaitable[None]] | None = None) -> None:
        
        self.on_finished = on_finished
        

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            voice_client = shared.discordvoice.client
            sink = shared.discordvoice.sink
            recording_finished = shared.discordvoice.recording_finished

        if not voice_client:
            raise Exception("Need to be in a voice channel.")
        
        if not sink or not voice_client.recording:
            raise Exception("Need to start recording first.")
        
        if not isinstance(sink, VADWaveSink):
            raise Exception("Sink is not a edgynodes.discordvoice VADWaveSink.")
        
        start = time.monotonic()

        await self.monitor_voice(sink.received_voice, recording_finished)

        print(f"Waited for voice for {time.monotonic() - start} seconds")

        if self.on_finished:
            await self.on_finished(state, shared)

    
    async def monitor_voice(self, recorded_voice: asyncio.Event, recording_finished: asyncio.Event) -> None:

        voice = asyncio.create_task(recorded_voice.wait())
        abort = asyncio.create_task(recording_finished.wait())  

        _, pending = await asyncio.wait(
            [voice, abort],
            return_when=asyncio.FIRST_COMPLETED
        )

        for t in pending:
            t.cancel()



class AwaitVoiceStopVADNode(Node[StateProtocol, SharedProtocol]):

    silence_timeout: float
    on_finished: Callable[[StateProtocol, SharedProtocol], Awaitable[None]] | None = None

    def __init__(self, silence_timeout: float = 1, on_finished: Callable[[StateProtocol, SharedProtocol], Awaitable[None]] | None = None) -> None:

        self.silence_timeout = silence_timeout
        self.on_finished = on_finished
        

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            voice_client = shared.discordvoice.client
            sink = shared.discordvoice.sink

        if not voice_client:
            raise Exception("Need to be in a voice channel.")
        
        if not sink or not voice_client.recording:
            raise Exception("Need to start recording first.")
        
        if not isinstance(sink, VADWaveSink):
            raise Exception("Sink is not a edgynodes.discordvoice VADWaveSink.")
        
        start = time.monotonic()

        await self.monitor_silence(voice_client, sink)

        print(f"[yellow]Waited for silence for {time.monotonic() - start:.2f}s.[/yellow]")
        
        if self.on_finished:
            await self.on_finished(state, shared)

    
    async def monitor_silence(self, voice_client: discord.VoiceClient, sink: VADWaveSink):

        while voice_client.recording:
            if time.monotonic() - sink.last_voice > self.silence_timeout:
                break

            await asyncio.sleep(0.1)

