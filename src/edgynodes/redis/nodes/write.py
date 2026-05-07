import edgygraph

from ..core.states import SharedProtocol, StateProtocol

class WriteNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    required_dependencies = {"redis"}

    async def __call__(self, state: T, shared: S) -> None:

        data = state.redis.write.pop(0)
        
        for key, value in data.items():
            await shared.redis.connection.set(key, value)

class WriteAllNode[T: StateProtocol = StateProtocol, S: SharedProtocol = SharedProtocol](edgygraph.Node[T, S]):

    required_dependencies = {"redis"}

    async def __call__(self, state: T, shared: S) -> None:

        while state.redis.write:
            data = state.redis.write.pop(0)
            
            for key, value in data.items():
                await shared.redis.connection.set(key, value)
