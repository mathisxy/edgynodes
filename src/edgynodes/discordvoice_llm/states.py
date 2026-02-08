import edgygraph

from ..discordvoice import StateAttribute as DiscordVoiceStateAttribute, SharedAttribute as DiscordVoiceSharedAttribute
from ..llm import StateAttribute as LLMStateAttribute, SharedAttribute as LLMSharedAttribute


class State(edgygraph.State):

    discordvoice: DiscordVoiceStateAttribute
    llm: LLMStateAttribute
    
class Shared(edgygraph.Shared):
    
    discordvoice: DiscordVoiceSharedAttribute
    llm: LLMSharedAttribute


