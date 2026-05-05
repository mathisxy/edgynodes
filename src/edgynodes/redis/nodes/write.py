import edgygraph

from ..core.states import SharedProtocol, StateProtocol

class WriteNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    required_dependencies = {"redis"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        data = state.redis.write.get()
        
        for key, value in data.items():
            await shared.redis.connection.set(key, value)

class WriteAllNode(edgygraph.Node[StateProtocol, SharedProtocol]):

    required_dependencies = {"redis"}

    async def __call__(self, state: StateProtocol, shared: SharedProtocol) -> None:

        while not state.redis.write.empty():
            data = state.redis.write.get()
            
            for key, value in data.items():
                await shared.redis.connection.set(key, value)
