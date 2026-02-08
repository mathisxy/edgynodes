import edgygraph

from ..discord import StateAttribute as DiscordStateAttribute, SharedAttribute as DiscordSharedAttribute
from ..discordmessage import StateAttribute as DiscordMessageStateAttribute, SharedAttribute as DiscordMessageSharedAttribute

class State(edgygraph.State):
    
    discord: DiscordStateAttribute
    discordmessage: DiscordMessageStateAttribute

class Shared(edgygraph.Shared):
    
    discord: DiscordSharedAttribute
    discordmessage: DiscordMessageSharedAttribute