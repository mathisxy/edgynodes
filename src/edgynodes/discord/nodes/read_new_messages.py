import edgygraph
from ..core.states import StateProtocol, SharedProtocol


class ReadNewMessagesNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    dependencies = {"py-cord"}

    def __init__(self, count: int = 20) -> None:
        super().__init__()
        self.count = count


    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            channel = shared.discord.text_channel
        
        async for msg in channel.history(limit=self.count, oldest_first=False):
            async with shared.lock:
                shared.discord.current_messages.append(msg)


