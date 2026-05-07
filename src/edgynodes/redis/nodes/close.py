import edgygraph

from ..core.states import StateProtocol, SharedProtocol

class CloseNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    required_dependencies = {"redis"}

    async def __call__(self, state: T, shared: S) -> None:

        await shared.redis.connection.aclose()