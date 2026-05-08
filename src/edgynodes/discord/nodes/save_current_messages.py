import edgygraph

from ..core.states import StateProtocol, SharedProtocol

class SaveNewMessagesNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    dependencies = {"py-cord"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:
            for msg in shared.discord.current_messages:
                if msg not in shared.discord.saved_messages:
                    shared.discord.saved_messages.append(msg)