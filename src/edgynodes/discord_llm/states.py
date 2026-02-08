import edgygraph

from ..discord import StateAttribute as DiscordStateAttribute, SharedAttribute as DiscordSharedAttribute
from ..llm import StateAttribute as LLMStateAttribute, SharedAttribute as LLMSharedAttribute


class State(edgygraph.State):
    
    discord: DiscordStateAttribute
    llm: LLMStateAttribute

class Shared(edgygraph.Shared):
    
    discord: DiscordSharedAttribute
    llm: LLMSharedAttribute