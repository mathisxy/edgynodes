import edgygraph
import discord


class State(edgygraph.State):
    pass

class Shared(edgygraph.Shared):
    discord_message: discord.Message