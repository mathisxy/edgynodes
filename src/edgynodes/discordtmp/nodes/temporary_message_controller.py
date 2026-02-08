from edgygraph import Node
from ..states import State, Shared

class ClearTmpDiscordMessagesNode(Node[State, Shared]):

    async def run(self, state: State, shared: Shared) -> None:

        async with shared.lock:

            keys = list(shared.discordtmp.controller.messages.keys())

            for key in keys:
                await shared.discordtmp.controller.delete(key)