from edgygraph import State, Shared
from llmir import AIMessages, Tool, AIChunkToolCall
from pydantic import Field
from typing import Callable, Any, Tuple
from .base_streams import LLMStream

class LLMState(State):
    llm_messages: list[AIMessages] = Field(default_factory=list[AIMessages])
    llm_new_messages: list[AIMessages] = Field(default_factory=list[AIMessages])

    llm_tools: list[Tool] = Field(default_factory=list[Tool])


class LLMShared(Shared):
    llm_stream: LLMStream | None = None

    llm_tool_functions: dict[str, Callable[..., Any]] = Field(default_factory=dict[str, Callable[..., Any]]) # name -> function

    llm_new_tool_calls: list[AIChunkToolCall] = Field(default_factory=list[AIChunkToolCall])
    llm_new_tool_call_results: list[Tuple[AIChunkToolCall, Any]] = Field(default_factory=list[Tuple[AIChunkToolCall, Any]])