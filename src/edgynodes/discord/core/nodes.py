from edgygraph import Node
from discord.abc import Messageable

from ..states import State, Shared


class StartTypingNode(Node[State, Shared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel


    async def run(self, state: State, shared: Shared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord.text_channel

            await shared.discord.typing.start(channel)

class StopTypingNode(Node[State, Shared]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel

    async def run(self, state: State, shared: Shared) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord.text_channel

            await shared.discord.typing.stop(channel)