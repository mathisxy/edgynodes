from edgygraph import Node
from discord.abc import Messageable

from .states import DiscordTextState, DiscordTextShared


class StartTypingNode(Node[DiscordTextState, DiscordTextShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel


    async def run(self, state: DiscordTextState, shared: DiscordTextShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_message.channel

            await shared.discord_typing.start(channel)

class StopTypingNode(Node[DiscordTextState, DiscordTextShared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel

    async def run(self, state: DiscordTextState, shared: DiscordTextShared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord_message.channel

            await shared.discord_typing.stop(channel)