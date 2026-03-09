from edgygraph import Stream
from llmir import AIChunks
import asyncio


class LLMStream(Stream[AIChunks]):
    abort: asyncio.Event

    def __init__(self) -> None:
        self.abort = asyncio.Event()