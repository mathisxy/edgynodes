from typing import Protocol, runtime_checkable

from ..discord import StateProtocol as DiscordStateProtocol, SharedProtocol as DiscordSharedProtocol
from ..llm import StateProtocol as LLMStateProtocol, SharedProtocol as LLMSharedProtocol


@runtime_checkable
class StateProtocol(DiscordStateProtocol, LLMStateProtocol, Protocol):
    pass

@runtime_checkable
class SharedProtocol(DiscordSharedProtocol, LLMSharedProtocol, Protocol):
    pass