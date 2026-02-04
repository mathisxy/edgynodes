from edgynodes.discord import DiscordTextState, DiscordTextShared # type: ignore
from edgynodes.llm import LLMState, LLMShared # type: ignore


class DiscordLLMState(LLMState, DiscordTextState):
    pass

class DiscordLLMShared(LLMShared, DiscordTextShared):
    pass