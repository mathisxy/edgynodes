import edgygraph
from ..core.states import StateProtocol, SharedProtocol


class AddNewMessages[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    dependencies = {"py-cord"}

    def __init__(self, count: int = 20) -> None:
        super().__init__()
        self.count = count


    async def __call__(self, state: T, shared: S) -> None:

        async with shared.lock:
            channel = shared.discord.text_channel
            current_ids = [m.id for m in shared.discord.messages]

        
        async for msg in channel.history(limit=self.count, oldest_first=False):
            async with shared.lock:
                if msg.id not in current_ids:
                    shared.discord.messages.append(msg)

