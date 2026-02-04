from edgynodes.discord import DiscordState, DiscordShared # type: ignore
from edgynodes.llm import LLMState, LLMShared # type: ignore


class DiscordLLMState(LLMState, DiscordState):
    pass

class DiscordLLMShared(LLMShared, DiscordShared):
    pass