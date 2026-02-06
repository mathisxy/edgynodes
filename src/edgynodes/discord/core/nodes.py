from edgygraph import Node
from discord.abc import Messageable

from .states import DiscordState, DiscordShared


class StartTypingNode(Node[DiscordState, DiscordShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel


    async def run(self, state: DiscordState, shared: DiscordShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_text_channel

            await shared.discord_typing.start(channel)

class StopTypingNode(Node[DiscordState, DiscordShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel

    async def run(self, state: DiscordState, shared: DiscordShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_text_channel

            await shared.discord_typing.stop(channel)