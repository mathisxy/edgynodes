from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol

class ClearTmpDiscordMessagesNode(Node[StateProtocol, SharedProtocol]):
    
    dependencies = {"py-cord"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:

            keys = list(shared.discordtmp.controller.messages.keys())

            for key in keys:
                await shared.discordtmp.controller.delete(key)