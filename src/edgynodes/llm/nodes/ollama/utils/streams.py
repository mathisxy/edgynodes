from typing import AsyncIterator
from types import TracebackType
from ollama import ChatResponse
from llmir import AIChunkText, AIChunks, AIChunkToolCall
from rich import print as rprint
from ....core.streams import LLMStream


class OllamaStream(LLMStream):
    iterator: AsyncIterator[ChatResponse]

    def __init__(self, iterator: AsyncIterator[ChatResponse]) -> None:
        super().__init__()
        self.iterator = iterator

    async def __anext__(self) -> AIChunks:
        if self.abort.is_set():
            print("Aborting Stream")
            raise StopAsyncIteration

        chunk: ChatResponse
        while True:
            try:
                chunk = await self.iterator.__anext__()
            except StopAsyncIteration:
                raise StopAsyncIteration

            message = chunk.message

            # Tool calls kommen bei Ollama vollständig in einem Chunk an –
            # kein Akkumulieren nötig wie bei OpenAI.
            if message.tool_calls:
                rprint("Received tool call: ", message.tool_calls)
                tool_call = message.tool_calls[0]
                return AIChunkToolCall(
                    id=tool_call.function.name,
                    name=tool_call.function.name,
                    arguments=dict(tool_call.function.arguments),
                )

            if message.content:
                return AIChunkText(text=message.content)

            # Leere Chunks (z.B. done-Marker) überspringen
            continue

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return await super().__aexit__(exc_type, exc, tb)

    async def aclose(self) -> None:
        await super().aclose()
        await self.iterator.aclose() # type: ignore
        print("aclose called")