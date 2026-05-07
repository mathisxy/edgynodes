import edgygraph

from ..core.states import StateProtocol, SharedProtocol


class ReadNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    required_dependencies = {"redis"}

    async def __call__(self, state: T, shared: S) -> None:
        
        key = state.redis.read.pop(0)
        value = await shared.redis.connection.get(key)
        if value is not None:
            state.redis.results[key] = value

class ReadAllNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    required_dependencies = {"redis"}

    async def __call__(self, state: T, shared: S) -> None:

        while state.redis.read:
            key = state.redis.read.pop(0)
            value = await shared.redis.connection.get(key)
            if value is not None:
                state.redis.results[key] = value
        
