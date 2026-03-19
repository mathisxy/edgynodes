import asyncio
import discord
import time

from edgygraph import Node

from ...core.states import StateProtocol, SharedProtocol
from .utils.vad_wave_sink import VADWaveSink


class AwaitVoiceStartVADNode(Node[StateProtocol, SharedProtocol]):

    dependencies = {"py-cord", "webrtcvad"}

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

    def __init__(self, silence_timeout: float = 1) -> None:

        self.silence_timeout = silence_timeout        

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

    
    async def monitor_silence(self, voice_client: discord.VoiceClient, sink: VADWaveSink):

        while voice_client.recording:
            if time.monotonic() - sink.last_voice > self.silence_timeout:
                break

            await asyncio.sleep(0.1)