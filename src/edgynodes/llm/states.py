import edgygraph as e
from llmir import AIMessages, Tool, AIChunkToolCall
from pydantic import Field
from typing import Callable, Any, Tuple, Protocol
from .core.streams import LLMStream

class StateAttribute(e.StateAttribute):
    messages: list[AIMessages] = Field(default_factory=list[AIMessages])
    new_messages: list[AIMessages] = Field(default_factory=list[AIMessages])

    tools: list[Tool] = Field(default_factory=list[Tool])


class SharedAttribute(e.SharedAttribute):
    stream: LLMStream | None = None

    tool_functions: dict[str, Callable[..., Any]] = Field(default_factory=dict[str, Callable[..., Any]]) # name -> function

    new_tool_calls: list[AIChunkToolCall] = Field(default_factory=list[AIChunkToolCall])
    new_tool_call_results: list[Tuple[AIChunkToolCall, Any]] = Field(default_factory=list[Tuple[AIChunkToolCall, Any]])


class StateProtocol(e.StateProtocol, Protocol):

    llm: StateAttribute

class SharedProtocol(e.SharedProtocol, Protocol):

    llm: SharedAttribute