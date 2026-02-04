from edgygraph import Node
import discord
import asyncio

from .states import DiscordVoiceState, DiscordVoiceShared


class JoinVoiceChannelNode(Node[DiscordVoiceState, DiscordVoiceShared]):


    async def run(self, state: DiscordVoiceState, shared: DiscordVoiceShared) -> None:

        async with shared.lock:
            voice_channel = shared.discord_voice_channel
            voice_client = shared.discord_voice_client

        if voice_client and voice_client.is_connected():
            return  # Already connected
        
        await voice_channel.connect()

        async with shared.lock:
            shared.discord_voice_client = voice_client


class LeaveVoiceChannelNode(Node[DiscordVoiceState, DiscordVoiceShared]):

    async def run(self, state: DiscordVoiceState, shared: DiscordVoiceShared) -> None:
        async with shared.lock:
            voice_client = shared.discord_voice_client

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        async with shared.lock:
            shared.discord_voice_client = None



class RecordVoiceNode(Node[DiscordVoiceState, DiscordVoiceShared]):

    finished_recording: asyncio.Event = asyncio.Event()

    async def run(self, state: DiscordVoiceState, shared: DiscordVoiceShared) -> None:
        if not shared.discord_voice_client:
            raise RuntimeError("Not connected to a voice channel.")
        
        async with shared.lock:
            voice_client = shared.discord_voice_client
        
        if not voice_client:
            raise Exception("Need to be in a voice channel to start recording!")
            

        voice_client.start_recording( # type: ignore
            discord.sinks.WaveSink(),  # The sink type to use.
            self.handle_voice,  # What to do once done.
            shared,
        )

        await self.finished_recording.wait()


    async def handle_voice(self, sink: discord.sinks.WaveSink, shared: DiscordVoiceShared) -> None:

        async with shared.lock:
            shared.discord_voice_sink = sink
        
        self.finished_recording.set()
        

        

