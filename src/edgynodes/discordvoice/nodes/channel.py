from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol


class JoinVoiceChannelNode(Node[StateProtocol, SharedProtocol]):

    dependencies = {"py-cord"}

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

    dependencies = {"py-cord"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        async with shared.lock:
            voice_client = shared.discordvoice.client

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

        async with shared.lock:
            shared.discordvoice.client = None