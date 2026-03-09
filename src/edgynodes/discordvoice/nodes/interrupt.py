from edgygraph import Node

from ..core.states import StateProtocol, SharedProtocol

class SetInterruptNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:

            shared.discordvoice.interrupt.set()


class ClearInterruptNode(Node[StateProtocol, SharedProtocol]):

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        async with shared.lock:

            shared.discordvoice.interrupt.clear()