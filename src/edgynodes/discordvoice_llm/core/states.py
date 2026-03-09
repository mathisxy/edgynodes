from typing import Protocol, runtime_checkable


from ..discordvoice import StateProtocol as DiscordVoiceStateProtocol, SharedProtocol as DiscordVoiceSharedProtocol
from ..llm import StateProtocol as LLMStateProtocol, SharedProtocol as LLMSharedProtocol

@runtime_checkable
class StateProtocol(DiscordVoiceStateProtocol, LLMStateProtocol, Protocol):
    pass
    

@runtime_checkable
class SharedProtocol(DiscordVoiceSharedProtocol, LLMSharedProtocol, Protocol):
    pass


