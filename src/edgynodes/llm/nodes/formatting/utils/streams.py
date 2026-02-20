from typing import Callable
from types import TracebackType
from llmir import AIChunks

from ...core.utils.streams import LLMStream


ChunkTransformer = Callable[[AIChunks], AIChunks | None]


class TransformStream(LLMStream):
    """
    A stream that transforms the chunks of another llm stream.

    If the transformer returns None, the chunk is filtered out.

    The abort event is shared with the inner stream.
    """
    
    _inner: LLMStream
    _transformer: ChunkTransformer

    def __init__(self, inner: LLMStream, transformer: ChunkTransformer) -> None:
        super().__init__()
        self._inner = inner
        self._transformer = transformer
        
        # Share abort event
        self.abort = inner.abort

    async def __anext__(self) -> AIChunks:
        while True:
            chunk = await self._inner.__anext__()
            
            result = self._transformer(chunk)
            
            if result is None:
                # Filtered out
                continue
            
            return result

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        return await self._inner.__aexit__(exc_type, exc, tb)

    async def aclose(self) -> None:
        await self._inner.aclose()