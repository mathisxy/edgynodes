import edgygraph

from ..core.states import StateProtocol, SharedProtocol


class ReadNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    required_dependencies = {"redis"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        key = state.redis.read.get()
        value = await shared.redis.connection.get(key)
        if value is not None:
            state.redis.results[key] = value

class ReadAllNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    required_dependencies = {"redis"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        while not state.redis.read.empty():
            key = state.redis.read.get()
            value = await shared.redis.connection.get(key)
            if value is not None:
                state.redis.results[key] = value
        
