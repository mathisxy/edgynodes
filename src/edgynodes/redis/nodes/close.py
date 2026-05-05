import edgygraph

from ..core.states import StateProtocol, SharedProtocol

class CloseNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    required_dependencies = {"redis"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        await shared.redis.connection.aclose()