from discord.abc import Messageable
from edgygraph import Node

from ..states import StateProtocol, SharedProtocol



class StartTypingNode(Node[StateProtocol, SharedProtocol]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel


    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord.text_channel

            await shared.discord.typing.start(channel)



class StopTypingNode(Node[StateProtocol, SharedProtocol]):

    _channel: Messageable | None

    def __init__(self, channel: Messageable | None = None) -> None:

        self._channel = channel

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:
        
        async with shared.lock:

            channel: Messageable = self._channel or shared.discord.text_channel

            try:
                await shared.discord.typing.stop(channel)
            except Exception as e:
                print(e)