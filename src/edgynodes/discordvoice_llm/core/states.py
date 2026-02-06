from edgynodes.discordvoice import DiscordVoiceState, DiscordVoiceShared # type: ignore
from edgynodes.llm import LLMState, LLMShared # type: ignore


class DiscordVoiceLLMState(DiscordVoiceState, LLMState):
    pass
class DiscordVoiceLLMShared(DiscordVoiceShared, LLMShared):
    pass


